# Handoff: smoke-testing the release pipeline, on a branch, not yet merged

## Current status
- `feature/version_bump_and_release_automation` (version-bump CI gate,
  `release.yml`, `publish.yml` temporarily disabled) is merged to `main`
  via PR #8. All 5 Dependabot CI-action bumps are merged too.
- After that merge, the user asked why no release had been created.
  Answer: `release.yml` worked exactly as designed - PR #8 never touched
  `pyproject.toml` (only CI/workflow scaffolding and docs), so it
  correctly never fired. The pipeline had never actually been exercised
  end to end.
- **On branch `feature/release_automation_smoke_test`, not yet pushed as
  of this writing**: a deliberate `pyproject.toml` version bump
  (0.1.0 -> 0.1.1) with no other code change, purely to give
  `release.yml` something to react to and prove the whole chain
  (version-bump check -> merge -> tag -> GitHub Release) actually works.
- Bundled into the same branch: the README's Effort Log table and CI/CD
  section had also gone stale (see "Known gap" below) - fixed in this
  branch rather than a separate PR.

## The effort log (git notes on refs/notes/effort)
- Fully documented in AGENTS.md's "Effort log" section - read that
  before touching it, it's detailed and the details matter.
- Survived a real data-loss incident earlier in this project's history
  (something in this environment repeatedly force-updated
  `refs/notes/effort`, destroying locally-added, not-yet-pushed notes).
  Fixed by a hard rule: always chain `git notes add` and its `git push`
  into one command, never two separate steps.
- Numbers are intentionally not duplicated in this file - they drift
  fast and this file would just go stale again. Query
  `refs/notes/effort` directly, or check the README/PR description,
  which are the actual sources of truth for current standing.
- The `.git/config` push/fetch refspecs for this ref are local and
  don't survive a fresh clone - AGENTS.md documents a startup check
  for this and the exact commands to paste (agents never run
  `git config` themselves).

## Known gap, now fixed going forward
- The README's Effort Log table and CI/CD section drifted out of sync
  with reality for several merged PRs - including all 5 Dependabot
  merges never showing up as a leaderboard row, and PR #8 adding
  `release.yml` without the README ever mentioning it. Same root cause
  as the earlier handoff-notes staleness: "keep it in sync" with no
  concrete trigger just doesn't fire in practice.
- Fixed the same way handoff notes were fixed: added a "Keeping the
  README in sync" section to AGENTS.md, tying README updates to
  concrete checkpoints (drafting/regenerating a PR description whose
  Running Total disagrees with the README, or any
  `.github/workflows/` file changing meaningfully) instead of a vague
  ongoing obligation.

## Suggested next step
- Push `feature/release_automation_smoke_test` and open the PR (title
  and description already drafted, waiting on the user). Once merged,
  confirm `release.yml` actually creates tag `v0.1.1` and a GitHub
  Release - this is the first real end-to-end test of the release
  automation added in PR #8, and nothing has confirmed it works yet.
- If it works: the pipeline is proven, and the "suggested next step"
  from here on is just normal project work again.
- If it doesn't: check the Actions run for `release.yml` on `main`
  first (tag-existence check, `gh release create` permissions) before
  assuming the version-bump/CI side is the problem.
