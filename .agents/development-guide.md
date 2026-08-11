# Development Guide

Practical guide for working on psilocybin. Written 2026-07-15. Read
[architecture-and-patterns.md](architecture-and-patterns.md) for the
internals and [critical-issues-and-fixes.md](critical-issues-and-fixes.md)
for the open hit list before making changes. Also read
[AGENTS.md](../AGENTS.md) - the versioning, effort-log, commit-authorship,
and style rules there are enforced (some by CI) and are not optional.

## Quick start

The canonical local setup mirrors CI. See the
[README](../README.md#development) for the commands and tooling needed.

As of this review all of the above pass (see
[project-status.md](project-status.md) for the exact results).

### If `pip`/`venv` are unavailable in your environment

The review environment had no `pip`, `venv`, `ensurepip`, or `uv`. If you
hit the same wall, bootstrap into a scratch target dir instead of a venv:

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')"
python3 get-pip.py --target /path/to/libs
PYTHONPATH=/path/to/libs python3 -m pip install --target /path/to/libs \
  pytest pytest-cov mypy bandit radon xenon /path/to/psilocybin
PYTHONPATH=/path/to/libs python3 -m pytest -v      # entry point auto-loads the plugin; do NOT add -p psilocybin.plugin
```

Gotchas learned the hard way:

- Install the package **non-editable** (pass the repo path, not `-e`) so the
  `pytest11` entry point registers and the marker/fixtures load. If you also
  pass `-p psilocybin.plugin` on top of that, pytest double-registers the
  plugin and dies with "Plugin already registered under a different name."
- Console-script tools (`ruff`, `twine`) install a launcher into
  `<libs>/bin`, but `pip --target` **skips** that dir if it already exists
  (e.g. from the get-pip bootstrap) unless you pass `--upgrade`. `ruff`
  cannot run as `python -m ruff` (it shells out to a bundled binary), so you
  need the `<libs>/bin/ruff` launcher. `mypy`, `bandit`, `radon`, `xenon`,
  and `pytest` all run fine as `python -m <tool>`.

## File structure and ownership

```
src/psilocybin/
  __init__.py      public API surface + __version__ (stale, see M1)
  exceptions.py    PsilocybinError / BadTripError / GuidelineViolation
  report.py        HallucinationEvent, TripReport
  psychonaut.py    the hallucination engine + mode constants + default pool
  guidelines.py    Guidelines dataclass + validate()
  tripsitter.py    the supervisor / context manager + watch() decorator
  plugin.py        pytest marker + trip_sitter/psychonaut fixtures
tests/
  test_psilocybin.py   the whole suite (19 tests)
  sample_app.py        tiny add()/greet() stand-in to hallucinate against
  __init__.py          (empty; makes tests an importable package)
.github/workflows/     ci.yml, release.yml, publish.yml
.agents/               these notes
```

Import-direction rule: `guidelines.py` and `tripsitter.py` depend on
`psychonaut.py`; `psychonaut.py` depends only on `report.py`. Keep the mode
constants in `psychonaut.py` to avoid an import cycle.

## Common tasks

- **Add a mutation strategy:** edit `_mutate` and its `_mutate_*` helpers in
  `psychonaut.py`. Preserve the "produces a different value" property for
  every input (the current gap is `+inf`/`-inf`, M2). Changing draw order
  will shift seeded test outcomes - re-baseline and note it.
- **Add a guideline:** add the field to `Guidelines`, validate it in
  `Guidelines.validate()`, and enforce it in `TripSitter._evaluate` (post
  cleanup). Do not enforce guidelines inside `Psychonaut`.
- **Add a hallucination mode:** add a constant to `VALID_MODES` in
  `psychonaut.py` and a branch to the `_wrap` decision ladder; thread it
  through `Guidelines.mode` and the plugin marker docstring.
- **Expose the exception pool through the marker:** it exists on
  `Psychonaut` but isn't surfaced via `Guidelines`/`guide()` yet - a clean
  first contribution.
- **Change the version:** required by CI (`version-bump` job) whenever you
  touch `src/` or the runtime `dependencies`/`requires-python`. Prefix the
  PR title `[X.Y.Z]` only on the PR that does the bump. Keep
  `__init__.__version__` in step (today it is not - fixing M1 removes this
  footgun).

## Critical code paths to understand first

1. [`Psychonaut._wrap`](../src/psilocybin/psychonaut.py#L141-L178) - the
   per-call decision ladder and where every RNG draw is spent. Everything
   about intensity, modes, and reproducibility flows through here.
2. [`Psychonaut.__enter__`/`__exit__`](../src/psilocybin/psychonaut.py#L180-L202)
   - patch application and teardown. The atomicity bug (H1) lives in
   `__enter__`.
3. [`TripSitter.__exit__`](../src/psilocybin/tripsitter.py#L63-L88) and
   [`_evaluate`](../src/psilocybin/tripsitter.py#L90-L104) - cleanup-then-judge
   ordering, allowed-exception suppression, `halt_on_bad_trip`.
4. [`TripSitter.watch`](../src/psilocybin/tripsitter.py#L106-L132) - the
   decorator form and its per-invocation report reset (contrast with the
   report accumulation on a reused sitter, L4).

## Debugging tips and pitfalls

- **A trip induced zero hallucinations and "passed" - is my code resilient
  or was nothing patched?** Suspect the autospec patch-site rule (M5): if the
  code-under-test imported the target by name (`from mod import fn`),
  patching `mod.fn` won't touch it. Point the target where the call is
  *looked up*, and check `report.count` / `report.summary()`.
- **A seeded test started failing after I edited `_mutate`.** Expected - the
  shared RNG stream means mutation changes shift every later draw. Re-derive
  the expected values under the new code and update the seeded assertions.
- **`BadTripError: no psychonaut configured`.** You entered a `TripSitter`
  without calling `.guide(...)` (or used the `trip_sitter` fixture with no
  `@pytest.mark.psilocybin` marker, L8).
- **State leaked between two trips on one sitter.** The `TripReport` is
  shared and not reset between `guide()`/`with` cycles (L4). Use `watch()`
  (fresh report per call) or a fresh `TripSitter` for isolation.
- **Don't** move guideline evaluation before unpatching, enforce limits
  inside `Psychonaut`, or weaken the forbidden-target pre-check - these are
  the load-bearing invariants (see
  [architecture-and-patterns.md](architecture-and-patterns.md)).

## Before you open a PR

Per [AGENTS.md](../AGENTS.md): bump the version if `src/`/runtime deps
changed; keep the README effort-log table, Top Agent badge, and CI/CD
section in sync; update [notes-for-next-agent.md](notes-for-next-agent.md);
add an effort note (chained add+push) for meaningful commits; author commits
as the agent+model; no emoji, no em/en dashes.
