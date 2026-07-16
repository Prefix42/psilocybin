# Architecture and Patterns

How psylocybin is put together and the invariants to preserve when touching
it. Written from a full read of the source on 2026-07-15. For the goals and
themes behind these choices see
[design-philosophy.md](design-philosophy.md); for the open defects in the
current implementation see
[critical-issues-and-fixes.md](critical-issues-and-fixes.md).

## Module map

| Module | Responsibility |
|---|---|
| [`exceptions.py`](../src/psylocybin/exceptions.py) | Error hierarchy: `PsylocybinError` -> `BadTripError` -> `GuidelineViolation`. |
| [`report.py`](../src/psylocybin/report.py) | `HallucinationEvent` (one induced glitch) and `TripReport` (events + timing + bad-trip verdict + `summary()`). |
| [`psychonaut.py`](../src/psylocybin/psychonaut.py) | `Psychonaut` - the actual patching/hallucination engine. Also owns the mode constants (`MODE_PER_CALL`, `MODE_SINGLE`, `VALID_MODES`) and `DEFAULT_EXCEPTION_POOL`. |
| [`guidelines.py`](../src/psylocybin/guidelines.py) | `Guidelines` dataclass + `validate()`. Imports the mode constants from `psychonaut` (note the dependency direction). |
| [`tripsitter.py`](../src/psylocybin/tripsitter.py) | `TripSitter` - the supervisor/context manager that enforces guidelines and guarantees cleanup. |
| [`plugin.py`](../src/psylocybin/plugin.py) | pytest integration: the `psylocybin` marker, the `trip_sitter` and `psychonaut` fixtures. Wired via the `pytest11` entry point in `pyproject.toml`. |
| [`__init__.py`](../src/psylocybin/__init__.py) | Public surface (`__all__`) and `__version__` (currently stale - see M1). |

Dependency direction worth remembering: `guidelines.py` imports from
`psychonaut.py` (for the mode constants), and `tripsitter.py` imports both.
`psychonaut.py` depends only on `report.py`. Keep the mode constants in
`psychonaut.py` to avoid a cycle.

## Pattern 1: nested context managers, cleanup-before-judgment

The whole safety story rests on two stacked context managers.

- `TripSitter` is the outer context manager. Its `__exit__`
  ([tripsitter.py L63-L88](../src/psylocybin/tripsitter.py#L63-L88)) does
  cleanup **first** (`self._psychonaut.__exit__(...)` unpatches everything),
  stamps `ended_at`, and only **then** calls `_evaluate(...)` to decide
  whether the trip was bad. This ordering is deliberate and load-bearing: a
  `BadTripError` is raised (if `halt_on_bad_trip`) only after the codebase is
  already sober, so a bad verdict never leaves things patched.
- `Psychonaut` is the inner context manager. `__enter__`
  ([L180-L196](../src/psylocybin/psychonaut.py#L180-L196)) starts an
  `unittest.mock.patch(..., autospec=True)` per target and installs a
  `side_effect` wrapper; `__exit__`
  ([L198-L202](../src/psylocybin/psychonaut.py#L198-L202)) stops every
  patcher in reverse order and clears the list.

**Invariant to preserve:** cleanup must run regardless of how the trip ends,
and must complete before any verdict is raised. Today this holds for the
*trip body* but NOT for a *setup* failure inside `Psychonaut.__enter__` -
see H1 in [critical-issues-and-fixes.md](critical-issues-and-fixes.md); the
`__enter__` loop is not atomic and can leak patches. Any change here must
keep (and ideally extend) the guarantee, not weaken it.

## Pattern 2: mock + autospec + `side_effect` delegating to the original

Each target is replaced by an autospec mock whose `side_effect` is a closure
built by [`_wrap`](../src/psylocybin/psychonaut.py#L141-L178). The closure
captures `original` (the true callable, grabbed via
`patcher.get_original()[0]` *before* `start()`), so calling `original(...)`
inside the wrapper invokes the real function, not the mock - no recursion.
When `side_effect` returns a value other than `mock.DEFAULT`, the mock hands
that value back to the caller, which is how both a normal pass-through and a
mutated return work.

`autospec=True` gives signature checking (you cannot hallucinate a call that
doesn't match the real signature) and restricts targets to importable
callables. Its flip side is the "patch where it's looked up" rule (M5): a
name already imported into the code-under-test's namespace is not affected.

## Pattern 3: the per-call decision, and where the RNG is spent

`_wrap`'s wrapper runs this ladder on every call while a trip is active
([L142-L176](../src/psylocybin/psychonaut.py#L142-L176)):

1. `if not self._active`: pass through (should only matter outside a trip).
2. `if mode == "single" and self._hallucinated`: pass through (budget spent).
3. Draw `self._rng.random()`; if `>= intensity`, pass through. Because
   `random()` is in `[0.0, 1.0)`, `intensity=1.0` always hallucinates and
   `intensity=0.0` never does.
4. Set `self._hallucinated = True`, then draw again: `< 0.5` -> return
   mutation, else -> exception injection.

The same `_rng` drives the intensity gate, the branch coin, the mutation
internals, and the exception choice. That is what makes a `seed` reproduce a
trip - but it also means **any change to mutation logic shifts the entire
downstream RNG stream**, so seeds are stable only within one code version.
Several tests pin specific seeds and assert exact outcomes; expect to
re-baseline them if you touch draw order.

## State lifecycle of a trip

```
TripSitter(guidelines)            # validate() once, fresh TripReport
   .guide(targets)                # forbidden-target check, build Psychonaut(report=self.report)
with sitter:                      # TripSitter.__enter__
   -> report.started_at = now
   -> psychonaut.__enter__        # _active=True, _hallucinated=False, patch each target
   ... code under test runs ...   # wrapper decides per call, records events on the shared report
                                  # TripSitter.__exit__
   -> psychonaut.__exit__         # unpatch all (reverse), _active=False
   -> report.ended_at = now
   -> _evaluate -> maybe bad_trip / BadTripError / suppress allowed exception
```

Key state owners:

- `Psychonaut._active` / `_hallucinated`: per-trip flags, reset in
  `__enter__`. `_hallucinated` is the `single`-mode budget.
- `TripReport`: owned by the `TripSitter`, **shared** into the `Psychonaut`
  via `guide()`. It is not reset between trips on the same sitter (only
  `started_at` is), so events accumulate across successive `guide()`/`with`
  cycles - see L4. The `watch()` decorator deliberately swaps in a fresh
  report per invocation for test isolation
  ([tripsitter.py L106-L132](../src/psylocybin/tripsitter.py#L106-L132)).

## The two hallucination modes, internally

Both modes share the exact same intensity gate; they differ only in step 2
of the ladder above.

- **`per_call`** (default): step 2 is a no-op, so every call is
  independently eligible for the whole trip. At `intensity=1.0`, every call
  hallucinates.
- **`single`**: once `_hallucinated` flips true, step 2 short-circuits all
  later calls to pass-through. At most one event per trip. The budget is
  enforced *inside* `Psychonaut` (not by the `TripSitter` aborting after the
  fact), and it resets each `__enter__`. Caveat: the budget is set in step 3
  *before* the mutation branch actually produces anything, so a
  mutation-branch call whose `original()` raises spends the budget silently
  (L3).

## Guideline enforcement (`TripSitter`)

- `forbidden_targets` is checked in `guide()` **before any patching**
  ([L35-L54](../src/psylocybin/tripsitter.py#L35-L54)), matching exact target
  or any dotted sub-path (`forbidden + "."`). This is the one guardrail that
  cannot be bypassed by a bad trip, by construction.
- `_evaluate` ([L90-L104](../src/psylocybin/tripsitter.py#L90-L104)) runs
  after cleanup and returns the first breached guideline's reason (duration,
  then count, then an escaped non-allowed exception), or `""`.
- `halt_on_bad_trip` chooses between raising `BadTripError` and merely
  recording the verdict on the report. When not halting, an escaped
  exception is swallowed (it is already captured as the reason).
- `allowed_exceptions` does double duty: it is both the set of exceptions
  that may escape without being a bad trip, and (when the trip is otherwise
  clean) the set that gets suppressed at `__exit__` so an expected
  hallucination exception doesn't fail the test.

## Invariants to maintain when editing

1. **Sobriety is guaranteed.** Every started patch must be stopped no matter
   how the trip (or its setup) ends. Fixing H1 is about extending this to the
   setup phase, never contracting it.
2. **Cleanup precedes judgment.** Do not move `_evaluate`/`BadTripError`
   ahead of the unpatch step.
3. **Forbidden targets are rejected before patching.** Keep that check in
   `guide()`, not later.
4. **A fresh trip starts sober.** `__enter__` must reset `_hallucinated`
   (and `_active`).
5. **Reproducibility is seed-scoped, not version-stable.** If you change RNG
   draw order or mutation logic, expect and re-baseline seeded tests, and say
   so in the change.

## Extension points (where future work naturally slots in)

- **Mutation strategies:** `_mutate` and its per-type helpers are the obvious
  place to add richer/typed perturbations (and to fix the inf no-op, M2).
- **Custom exception pools:** already a `Psychonaut` constructor argument but
  not surfaced through `Guidelines`/the marker - a natural thing to expose.
- **New modes:** add a constant to `VALID_MODES` and a branch in the `_wrap`
  ladder; keep the constants in `psychonaut.py`.
- **Reporting:** `TripReport.summary()` is plain text; structured output
  (JSON) for CI consumption is a clean addition.
- **Async/thread support:** would require guarding the gate+draw section
  (M4) rather than a new API.
