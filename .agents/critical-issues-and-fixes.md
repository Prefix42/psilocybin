# Critical Issues and Fixes (Review Hit List)

Populated by a full project review on 2026-07-15. See
[code-review-2026-07-15.md](code-review-2026-07-15.md) for the review scope,
method, and the exact commands/probes run to confirm each item below.

## Status at a glance

Contrary to a "assume nothing works" starting stance, the code is in good
empirical shape as of this review:

- `pytest`: **19 passed** (Python 3.13).
- `ruff check` / `ruff format --check`: clean.
- `mypy src`: clean (no issues in 7 files).
- `bandit`: no issues. `radon`: average complexity A (2.9), worst block B.
  `xenon --max-absolute B --max-modules A --max-average A`: passes.

So every item here is a **latent** bug, fragility, or documentation/design
deviation - not an active test failure - **except H1**, which is a real,
reproduced defect that simply has no test covering it. Nothing has been
fixed; this file is the recommendation list. No code changes were made in
producing it.

Severity key: HIGH = correctness/safety defect or broken core promise;
MEDIUM = latent bug, real fragility, or undocumented sharp edge users will
hit; LOW = polish, minor mismatch, or packaging nicety.

---

## HIGH

### H1. `Psychonaut.__enter__` is not atomic - a failed target leaves earlier targets permanently patched and actively hallucinating

- Location: [psychonaut.py L180-L196](../src/psylocybin/psychonaut.py#L180-L196)
- The core promise, stated in the README ("guarantees the codebase is
  restored to normal when the trip ends, whether it ended cleanly or not")
  and the class docstrings, is that a trip never leaves the codebase in a
  hallucinating state. `__enter__` breaks this on a multi-target trip:

  ```python
  for target_path in self.targets:
      try:
          patcher = patch(target_path, autospec=True)
          original = patcher.get_original()[0]
      except (AttributeError, ImportError, TypeError) as e:
          raise ValueError(f"Failed to patch target '{target_path}': ...") from e
      mock_obj = patcher.start()          # target N started + appended
      mock_obj.side_effect = self._wrap(target_path, original)
      self._patchers.append(patcher)
  ```

  If any target after the first raises (e.g. a typo'd or missing dotted
  path), the exception propagates out of `Psychonaut.__enter__` -> out of
  `TripSitter.__enter__` -> out of the `with` statement. Because `__enter__`
  raised, Python never calls the matching `__exit__`, so the patchers
  already `.start()`ed for earlier targets are **never stopped**, and
  `self._active` (set True at the top of `__enter__`) is never reset.
- **Reproduced.** Guiding `["tests.sample_app.add", "tests.sample_app.nope"]`
  then entering: the enter raises `ValueError` (good), but afterward
  `sample_app.add` is still the mock, `psychonaut._active` is still `True`,
  and six subsequent `add(2, 2)` calls returned `5, 3, 5` and raised
  `ValueError` twice - never the real `4`. The code-under-test's module is
  left corrupted and actively hallucinating for the rest of the process,
  with no `with`-block left to clean it up.
- **Recommended fix:** make `__enter__` roll back on failure - wrap the loop
  so that if any target fails, every already-started patcher is
  `.stop()`ed and `_active`/`_patchers` are reset before re-raising. Prefer
  validating/patching all targets first and only marking `_active = True`
  once every patch has succeeded. Add a regression test with a valid target
  followed by an invalid one asserting the valid target is restored.
- Note: `TripSitter`'s own forbidden-target check runs at `guide()` time
  (good, per Design notes), but that does not help here - this failure is at
  patch-application time inside `__enter__`, which has no such safety net.

---

## MEDIUM

### M1. `__version__` is out of sync with `pyproject.toml`

- Location: [`__init__.py` L46](../src/psylocybin/__init__.py#L46)
  (`__version__ = "0.1.0"`) vs [`pyproject.toml` L3](../pyproject.toml#L3)
  (`version = "0.1.2"`).
- **Reproduced.** A build/install of the package reports dist version
  `0.1.2` (the pytest banner shows `psylocybin-0.1.2`) while
  `import psylocybin; psylocybin.__version__` returns `'0.1.0'`. The runtime
  attribute lies about the installed version.
- This is more than cosmetic here: the entire release-automation system
  (see [AGENTS.md](../AGENTS.md) "Versioning") is built around bumping
  `pyproject.toml`'s version, yet nothing keeps `__init__.__version__` in
  step, and there is no CI check for the drift. Every version bump since
  0.1.0 has widened the gap.
- **Recommended fix:** stop hard-coding the version in two places. Read it
  at runtime from installed metadata
  (`importlib.metadata.version("psylocybin")`), or make `pyproject.toml`
  source the version dynamically from `__init__.__version__`
  (`[project] dynamic = ["version"]` + a setuptools `attr:` directive).
  Whichever direction, add it to the version-bump discipline so the two can
  never diverge again.

### M2. Float mutation can be a silent no-op (records a "hallucination" that changed nothing)

- Location: [`_mutate_float` L110-L127](../src/psylocybin/psychonaut.py#L110-L127).
- `_mutate`'s implied contract (asserted all over the tests: "should produce
  a different value") does **not** hold for several float inputs, across more
  than one branch:
  - **`0.0` (the most common case):** the negate branch returns `-0.0`, and
    `-0.0 == 0.0`; the `choice == 3` multipliers `0.0`/`-0.0` also yield a
    value equal to `0.0`. So a real return of `0.0` is frequently "mutated"
    to itself.
  - **`+inf`/`-inf`:** `choice == 3` with multiplier `0.5` or `2.0` leaves
    `inf` unchanged (`inf * 0.5 == inf`, `inf * 2.0 == inf`).
  - **Very large finite floats:** the `choice == 2` `value + 1.0` branch is a
    no-op (`1e308 + 1.0 == 1e308`).
- **Reproduced.** `-0.0 == 0.0` is `True`; `1e308 + 1.0 == 1e308` is `True`;
  and `_mutate(0.0)` returned a value equal to `0.0` for **26 of the first
  50 seeds**. `+inf`/`-inf` no-op via 2 of the 4 `choice == 3` multipliers.
  [`test_infinity_is_mutated`](../tests/test_psylocybin.py#L305-L323) passes
  only because its fixed `seed=100` happens to dodge the no-op branch
  (observed `+inf -> 0.0`, `-inf -> nan`);
  [`test_float_mutations_handle_special_values`](../tests/test_psylocybin.py#L247-L261)
  only asserts `isinstance(..., float)` for `0.0`, so it never catches the
  no-op at all.
- **Real-world impact (not just a flaky test):** when the return-mutation
  branch produces the same value, `_wrap` still records a `HallucinationEvent`
  (`return_mutation`, detail e.g. `0.0 -> -0.0`). The report then claims a
  hallucination occurred when the value handed to the caller was effectively
  unchanged - false confidence that the code was exercised against a
  perturbed value.
- **Historical note:** `AGENTS.md`'s commit-style example
  (`[1.0.0] Fix the mutation strategy for negative zero`) suggests this class
  of bug was noticed before; it is not fully resolved.
- **Recommended fix:** guarantee the property centrally - after choosing a
  mutation, verify it differs from the input (using `math.copysign`/`is`
  semantics for `0.0` vs `-0.0`, and finiteness checks) and fall back to a
  known-different value otherwise. Special-case non-finite and zero floats in
  `_mutate_float` the way `nan -> 0.0` already is. Then make the tests
  property-based/seed-independent instead of relying on lucky seeds.

### M3. `test_empty_allowed_exceptions_does_not_crash` is seed-fragile and asserts the wrong thing

- Location: [`test_psylocybin.py` L127-L144](../tests/test_psylocybin.py#L127-L144).
- The test does a single `add(1, 1)` at `intensity=1.0` and asserts it raises
  `BadTripError`. But a hallucination is a 50/50 coin flip between
  return-mutation and exception-injection. Only the exception branch produces
  an escaping exception that (with empty `allowed_exceptions`) becomes a bad
  trip. If the coin lands on return-mutation, no exception escapes, `_evaluate`
  sees `exc_type is None`, there is no bad trip, and `pytest.raises` fails.
- **Reproduced.** At `seed=6` the branch draw is `0.82` (>= 0.5 -> exception
  branch), so it passes today - purely by seed luck. The test name
  ("does not crash") and its assertion (must raise `BadTripError`) also
  disagree about intent.
- **Recommended fix:** force the exception path deterministically (e.g. a
  `Psychonaut` whose only reachable hallucination is an exception, or drive
  enough iterations that an exception is statistically guaranteed and assert
  on that), and rename the test to match what it actually verifies.

### M4. Not safe for concurrent code-under-test (undocumented)

- Location: shared mutable state on `Psychonaut` -
  [`_active`/`_hallucinated`/`_rng` L82-L84](../src/psylocybin/psychonaut.py#L82-L84),
  consumed in [`_wrap` L141-L178](../src/psylocybin/psychonaut.py#L141-L178).
- A single `random.Random` plus plain instance flags drive every wrapped
  call. If the code being fuzzed calls targets from multiple threads (or
  overlapping async tasks), the RNG draws interleave nondeterministically
  (defeating `seed` reproducibility) and `single`-mode's `_hallucinated`
  gate races (more than one hallucination can slip through, or the count is
  wrong). Nothing in the README or docstrings flags this.
- **Recommended fix:** document the single-threaded assumption prominently,
  and/or guard the gate+draw critical section with a lock if concurrent
  targets are meant to be supported.

### M5. `autospec` patch-site semantics will surprise users (undocumented gotcha)

- Location: [`__enter__` L185](../src/psylocybin/psychonaut.py#L185) uses
  `patch(target_path, autospec=True)`.
- Patching happens at the definition site. If the code-under-test did
  `from myapp.inventory import reserve_item` and calls the bare name, that
  name was bound at import time and is unaffected by patching
  `myapp.inventory.reserve_item` - the trip will silently induce zero
  hallucinations and look like a clean pass. This is the standard
  `unittest.mock.patch` "patch where it's looked up" rule, but the README's
  Design notes only mention the positive constraint (target must be
  importable), not this failure mode.
- **Recommended fix:** add a short "where to point a target" note to the
  README/docs, mirroring mock's own guidance, so a no-op trip isn't
  mistaken for a resilient codebase.

---

## LOW

### L1. `_mutate(None)` returns `0`, contradicting the documented "truthy surprise"

- Location: [`psychonaut.py` L102-L103](../src/psylocybin/psychonaut.py#L102-L103).
  README [L139](../README.md#L139) and the `__init__` docstring both say
  "`None` replaced with a truthy surprise." The code returns `0`, which is
  falsy. **Reproduced:** `_mutate(None) == 0`, `bool(0) is False`.
- It is still a mutation (`0 != None`), so
  [`test_mutation_actually_changes_values`](../tests/test_psylocybin.py#L217-L244)
  passes - but the docs are wrong, and `0` collides with a perfectly ordinary
  real return value. **Fix:** either return an actually-truthy sentinel to
  match the docs, or correct the docs to say `None -> 0`.

### L2. Dead/misleading `try/except` in `_wrap`

- Location: [`psychonaut.py` L152-L157](../src/psylocybin/psychonaut.py#L152-L157).
  `try: result = original(...) except Exception: raise` re-raises with no
  handling - it does nothing a plain call wouldn't. The comment claims it
  prevents recording the original's exception as a hallucination, but that
  is already guaranteed by ordering (the `record()` call is after the
  mutation). **Fix:** drop the `try/except` and keep a one-line comment, or
  make the intent real (see L3).

### L3. `single`-mode budget can be spent without recording a hallucination

- Location: [`psychonaut.py` L150-L166](../src/psylocybin/psychonaut.py#L150-L166).
  `self._hallucinated = True` is set *before* the return-mutation branch
  calls `original(...)`. If that call raises a real exception, the budget is
  consumed (so no later call can hallucinate in `single` mode) yet no
  `HallucinationEvent` is recorded - the trip can report zero hallucinations
  even though one was "used." **Fix:** set `_hallucinated = True` only after a
  hallucination is actually produced (mutation returned, or exception
  injected).

### L4. Report accumulates across trips on a reused `TripSitter` (surprising vs "resets")

- Location: [`TripSitter.guide` L42-L54](../src/psylocybin/tripsitter.py#L42-L54)
  passes `report=self.report`, and `__enter__` only resets `started_at`, not
  `events`. So a second `guide()`/`with` on the same sitter keeps
  accumulating events.
  [`test_single_mode_resets_between_separate_trips`](../tests/test_psylocybin.py#L99-L116)
  bakes this in (expects `count == 2`, i.e. 1 + 1). The `single`-mode
  *budget* resets per trip, but the *report* does not - the naming invites
  confusion. **Fix:** document the distinction clearly (see
  [architecture-and-patterns.md](architecture-and-patterns.md)), or reset the
  report per trip and adjust the test.

### L5. Missing `LICENSE` file

- `pyproject.toml` declares `license = { text = "MIT" }` but there is no
  `LICENSE` file in the tree. **Fix:** add the MIT license text as `LICENSE`
  so the distribution and the repo actually carry it.

### L6. No `py.typed` marker despite full typing

- The package is fully annotated and passes `mypy`, but ships no `py.typed`
  file, so downstream users get no types (PEP 561). Low priority for a test
  tool, but trivial to add. **Fix:** add `src/psylocybin/py.typed` and
  include it in the package data.

### L7. `_evaluate` reason precedence can report a less-relevant cause

- Location: [`tripsitter.py` L90-L104](../src/psylocybin/tripsitter.py#L90-L104).
  Checks are ordered duration -> hallucination count -> escaped exception,
  first match wins. When more than one guideline is breached at once, the
  reported `bad_trip_reason` may not be the most salient one. Minor;
  document or make the message list all breaches.

### L8. `trip_sitter` fixture used without a marker fails on `with`

- Location: [`plugin.py` L42-L55](../src/psylocybin/plugin.py#L42-L55).
  With no `@pytest.mark.psylocybin`, `targets` is empty, `guide()` is never
  called, and entering the sitter raises `BadTripError("no psychonaut
  configured")`. Probably intended, but easy to trip over. **Fix:** document
  that the marker (or an explicit `.guide(...)`) is required, or make a
  markerless fixture a clean no-op trip.

### L9. `HallucinationEvent.timestamp` is a monotonic value, not a wall-clock timestamp

- Location: [`report.py` L15](../src/psylocybin/report.py#L15) uses
  `default_factory=monotonic`. The field name reads like an epoch timestamp
  but is a monotonic clock reading (correct for durations, meaningless as a
  date). Minor naming/clarity issue.

### L10. Return-mutation runs the target's side effects; exception-injection skips them

- Location: [`_wrap` L151-L176](../src/psylocybin/psychonaut.py#L151-L176).
  The mutation branch calls `original(...)` (side effects happen, then the
  return is perturbed); the exception branch never calls `original` (side
  effects skipped). This is a reasonable design, but it means the two
  hallucination kinds exercise different code paths in the target. Worth a
  one-line note in the docs so users understand what a hallucination does
  and does not run.

### L11. `mypy` type-checks against 3.10 while the package floor is 3.9

- Location: [`pyproject.toml` L57](../pyproject.toml#L57)
  (`[tool.mypy] python_version = "3.10"`) vs
  [L6](../pyproject.toml#L6) (`requires-python = ">=3.9"`) and
  [L47](../pyproject.toml#L47) (`[tool.ruff] target-version = "py39"`).
- mypy would not catch a construct that is valid in 3.10 but breaks on 3.9,
  even though the CI test matrix and the metadata both claim 3.9 support.
  No such construct is present today, so this is latent, not an active
  break. **Fix:** set `python_version = "3.9"` to match the real floor.

### L12. README says "collections emptied" but empty collections are filled

- Location: README [L136-L139](../README.md#L136-L139) ("collections
  emptied") vs [`_mutate_list`/`_mutate_tuple`/`_mutate_dict`
  L132-L139](../src/psylocybin/psychonaut.py#L132-L139).
- **Reproduced.** Non-empty collections are emptied, but *empty* ones are
  filled: `_mutate([]) == [None]`, `_mutate(()) == (None,)`,
  `_mutate({}) == {"hallucinated": True}`. The README describes only half
  the behavior. **Fix:** reword to "collections emptied, or filled if
  already empty," or similar.

---

## Documentation-integrity issues

These live in `.agents/` itself and are the most actionable part of this
review, since the task was documentation. Tracked separately in
[project-status.md](project-status.md) and fixed/flagged in
[README.md](README.md).

- **D1.** `.agents/README.md` (as originally written) claimed
  `critical-issues-and-fixes.md`, `architecture-and-patterns.md`,
  `development-guide.md`, and `project-status.md` all had rich content
  ("4 HIGH severity issues with code examples", "5 MEDIUM severity issues",
  "Deep dive into design patterns", etc.) and that a code review was
  "complete" and the project "Ready for PR or deployment." In fact all four
  were empty placeholders and no such review was recorded. This review
  fills them in and corrects the index.
- **D2.** `.agents/README.md` was titled "Copilot Handoff Notes" / "For
  Copilot", but the project is now predominantly Claude-driven (per the
  README effort log) and `AGENTS.md` is deliberately agent-neutral.
- **D3.** `.agents/README.md` told contributors to "create a `NOTES.md`",
  which conflicts with `AGENTS.md`'s established
  [notes-for-next-agent.md](notes-for-next-agent.md) as the single living
  handoff doc.
- **D4.** Root `README.md`'s "truthy surprise" claim (see L1) is a
  user-facing doc bug.
- **D5.** No CI enforces the effort-log / README-sync / handoff-notes
  conventions (already noted in
  [notes-for-next-agent.md](notes-for-next-agent.md); repeated here because
  it is a standing gap, not a fixed one).

---

## Test-coverage gaps (no assertion exists today)

Not bugs, but blind spots a future contributor should close - several of
them would have caught items above:

- The H1 multi-target patch-leak path (no test guides more than one target,
  let alone a failing second one).
- `halt_on_bad_trip=False` - the "record the bad trip but swallow the
  exception" path in [`__exit__` L76-L80](../src/psylocybin/tripsitter.py#L76-L80).
- `max_duration_seconds` breach (the duration check in `_evaluate`).
- Forbidden **sub-path** matching (`target.startswith(forbidden + ".")` at
  [`tripsitter.py` L37](../src/psylocybin/tripsitter.py#L37)) - only exact
  matches are tested.
- The `<hallucinated {type}>` fallback branch in `_mutate` for unknown
  types ([`psychonaut.py` L104](../src/psylocybin/psychonaut.py#L104)).
- `GuidelineViolation` vs `BadTripError` distinction (tests only ever catch
  the base `BadTripError`).
