# Project Status

Current state of psilocybin. This file is the evergreen snapshot; for the
live, session-by-session handoff see
[notes-for-next-agent.md](notes-for-next-agent.md), and for the dated review
that produced this snapshot see
[code-review-2026-07-15.md](code-review-2026-07-15.md).

Last reviewed: **2026-07-15** (full read + local run of the whole toolchain).

## Empirical state (verified 2026-07-15)

All quality gates pass on Python 3.13:

| Check | Result |
|---|---|
| `pytest` | 19 passed |
| `ruff check .` | clean |
| `ruff format --check .` | clean (10 files already formatted) |
| `mypy src` | clean (no issues in 7 files) |
| `bandit -c pyproject.toml -r src` | no issues |
| `radon cc src -a` | average complexity A (2.9); worst block B |
| `xenon --max-absolute B --max-modules A --max-average A src` | passes |

So the earlier handoff's "assume nothing works" framing does not match
reality: the suite is green and the tooling gates hold. What the review
found instead is a set of **latent** issues and doc/design deviations,
catalogued in [critical-issues-and-fixes.md](critical-issues-and-fixes.md).

## What is done

- Core engine (`Psychonaut`), supervisor (`TripSitter`), config
  (`Guidelines`), reporting (`TripReport`), exceptions, and the pytest
  plugin are all implemented and working.
- Both hallucination modes (`per_call`, `single`) work as documented.
- CI matrix (3.9-3.13) plus lint/type/complexity/security/secrets gates and
  a `version-bump` gate are wired and, per the handoff notes, green on
  `main`.
- Release automation (tag + GitHub Release + build/`twine check` on a
  version bump) is proven end-to-end; the `GITHUB_TOKEN` anti-recursion
  footgun is understood and worked around (see
  [notes-for-next-agent.md](notes-for-next-agent.md) and `AGENTS.md`).
- PyPI/TestPyPI **upload** steps remain intentionally disabled (`if: false`)
  pending the user's call.

## Open items (from this review)

Full detail, evidence, and recommended fixes in
[critical-issues-and-fixes.md](critical-issues-and-fixes.md). Headlines:

- **HIGH - H1:** `Psychonaut.__enter__` is not atomic; a failed target on a
  multi-target trip leaves earlier targets permanently patched and actively
  hallucinating. Reproduced. Violates the project's core safety promise. No
  test covers it. This is the top fix.
- **MEDIUM:** `__version__` drift (0.1.0 vs 0.1.2, M1); float mutation
  silent no-op for `0.0`/`-0.0`/`inf`/large floats - records a "hallucination"
  that changed nothing, and tests pass only on lucky seeds (M2);
  seed-fragile `test_empty_allowed_exceptions_does_not_crash` (M3);
  undocumented non-thread-safety (M4); undocumented autospec patch-site
  gotcha (M5).
- **LOW:** `_mutate(None) -> 0` vs docs' "truthy surprise" (L1); dead
  `try/except` in `_wrap` (L2); `single`-budget spent without recording
  (L3); report accumulates across trips (L4); missing `LICENSE` (L5); no
  `py.typed` (L6); reason precedence (L7); markerless fixture (L8);
  monotonic "timestamp" naming (L9); mutation-vs-exception side-effect
  asymmetry (L10); mypy targets 3.10 while floor is 3.9 (L11); README
  "collections emptied" imprecision (L12).
- **Documentation integrity (D1-D5):** the `.agents/README.md` originally
  claimed four placeholder docs were complete and a review was done; those
  placeholders are now filled and the index corrected. The root README's
  "truthy surprise" line is still a doc bug (L1). No CI enforces the
  effort-log / README-sync / handoff conventions (standing gap, D5).

## Test-coverage gaps

No assertions currently exist for: the H1 multi-target leak,
`halt_on_bad_trip=False`, `max_duration_seconds` breach, forbidden
sub-path matching, the `<hallucinated {type}>` fallback, and the
`GuidelineViolation` vs `BadTripError` distinction. See the bottom of
[critical-issues-and-fixes.md](critical-issues-and-fixes.md).

## Deployment readiness

- **As a working pytest tool locally:** ready - installs, plugin loads, all
  gates pass.
- **As a published package:** not yet, and by design. Uploads are disabled,
  `__version__` lies (M1), and there is no `LICENSE` file (L5). Close M1 and
  L5 before any real publish, and treat re-enabling the upload steps as the
  user's decision, not an agent's.
- **Highest-value fix regardless of publishing:** H1, because it silently
  corrupts a user's code-under-test and breaks the one guarantee the tool
  makes.

## How to continue

- **Fixing bugs:** start from
  [critical-issues-and-fixes.md](critical-issues-and-fixes.md), take H1
  first, add the missing regression test alongside the fix, bump the version
  (CI requires it for `src/` changes), and re-baseline any seeded tests you
  perturb.
- **Docs/process work:** keep the README leaderboard/CI section and the
  handoff notes in sync per `AGENTS.md`.
- **Deciding on publishing or CI-enforcement of the conventions:** user's
  call - surface, don't assume.
