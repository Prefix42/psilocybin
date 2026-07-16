# Code Review - 2026-07-15

A full project review: understand the goal, design philosophy, and themes,
then produce a documentation hit list of bugs / design deviations. No code
was changed. This file records the scope, method, and evidence; the findings
themselves live in
[critical-issues-and-fixes.md](critical-issues-and-fixes.md), and the
understanding in [design-philosophy.md](design-philosophy.md),
[project-overview.md](project-overview.md), and
[architecture-and-patterns.md](architecture-and-patterns.md).

## Scope

- Every source file under `src/psylocybin/`, the full test suite, and
  `tests/sample_app.py`.
- `pyproject.toml`, all three GitHub workflows, `dependabot.yml`,
  `.gitignore`, both `README.md`s, `AGENTS.md`, `CLAUDE.md`.
- All existing `.agents/` notes (four of which were empty placeholders).

## Method

The task framing was "assume all code is untested and does not work." Rather
than assume, the review established ground truth empirically, then read
critically for latent issues the passing tests do not cover.

1. **Static read** of all sources and docs, mapping the metaphor onto the
   mechanics and looking for invariant violations, doc/behavior mismatches,
   and fragile tests.
2. **Toolchain run.** The environment had no `pip`/`venv`/`uv`, so `pip` was
   bootstrapped via `get-pip.py` into a scratch target dir and the package +
   dev tools were installed non-editable (so the `pytest11` entry point
   registers). Then the full CI-equivalent toolchain was run: `pytest
   --cov`, `ruff check`, `ruff format --check`, `mypy src`, `radon cc`,
   `xenon`, `bandit`.
3. **Targeted probes** to confirm suspected latent issues that no test
   exercises (below).

## Results

Every gate passed: **pytest 19/19**, ruff clean, ruff format clean, mypy
clean, bandit clean, radon avg A (2.9), xenon passes. The "nothing works"
premise did not hold - the value of the review is the latent issues behind
the green suite.

### Probe evidence

- **Partial-patch leak (H1).** Guided two targets, the second invalid, and
  entered. The enter raised `ValueError` as intended, but afterward
  `psychonaut._active` was still `True`, `sample_app.add` was still the mock,
  and six `add(2, 2)` calls returned `5, 3, 5` and raised `ValueError` twice
  - never the real `4`. The first target was never unpatched and kept
  actively hallucinating. Confirms H1 as a real, reproduced defect.
- **`__version__` skew (M1).** Installed dist reports `0.1.2` (pytest banner:
  `psylocybin-0.1.2`) while `psylocybin.__version__` returns `'0.1.0'`.
- **Infinity mutation no-op (M2).** Of the four `choice == 3` multipliers,
  `0.5` and `2.0` both leave `+inf` equal to `+inf`.
  `test_infinity_is_mutated` passes only because its `seed=100` happens to
  avoid that branch (observed `+inf -> 0.0`, `-inf -> nan`).
- **Seed-fragile test (M3).** At `seed=6` the branch draw is `0.82`, landing
  on the exception branch, which is the only reason
  `test_empty_allowed_exceptions_does_not_crash` currently raises
  `BadTripError`. A return-mutation outcome would make it fail.
- **"Truthy surprise" mismatch (L1).** `_mutate(None) == 0`, and `bool(0)` is
  `False`, contradicting the README/docstring.

### Reproduction commands

The scratch harness that produced the above (bootstrap pip, install, run all
gates, run the probes) is not committed; the essential invocation once tools
are installed is simply the Quick start block in
[development-guide.md](development-guide.md). The probes are described inline
in [critical-issues-and-fixes.md](critical-issues-and-fixes.md) precisely
enough to re-run by hand.

## Deliverables from this session

- Filled the four placeholder docs:
  [critical-issues-and-fixes.md](critical-issues-and-fixes.md) (the hit
  list), [architecture-and-patterns.md](architecture-and-patterns.md),
  [development-guide.md](development-guide.md),
  [project-status.md](project-status.md).
- Added [design-philosophy.md](design-philosophy.md) (goal / philosophy /
  themes) and this review record.
- Corrected [README.md](README.md) (the `.agents` index): it had claimed the
  placeholders were complete and a review was already done.
- Updated [notes-for-next-agent.md](notes-for-next-agent.md) with this
  session.

## Explicitly out of scope

- No source, test, or workflow files were modified - documentation only.
- No fixes applied; H1 and the rest remain open for a future session that
  can also add the missing regression tests and the required version bump.
