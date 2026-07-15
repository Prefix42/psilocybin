# Handoff: release automation now actually builds on release, on a branch, not yet merged

## Current status
- PR #9 (`feature/release_automation_smoke_test`) is merged to `main`.
  It bumped `pyproject.toml` to 0.1.1 purely to smoke-test the release
  pipeline added in PR #8, and separately resynced the README's stale
  Effort Log/CI-CD section. `release.yml` fired correctly and created
  tag `v0.1.1` and a GitHub Release - the tag-and-release half of the
  pipeline is now proven.
- That smoke test also surfaced a real, previously-undetected bug: the
  release it created never triggered `publish.yml`'s `release:
  types: [published]` trigger. Root cause: `release.yml` creates the
  release using the automatic `secrets.GITHUB_TOKEN`, and GitHub
  deliberately blocks events triggered by `GITHUB_TOKEN` from starting
  other workflow runs (anti-recursion safeguard). This meant even
  `publish.yml`'s harmless `build`/`twine check` job - not just the
  already-disabled PyPI upload steps - had never actually run.
- **On branch `feature/fold_publish_build_into_release`, not yet pushed
  as of this writing**: fixed by moving the build/`twine check` step
  directly into `release.yml` as a `build` job that runs right after
  `tag-and-release` (only when a release was actually created).
  `publish.yml` no longer listens for `release: published` at all -
  it's reachable only via manual `workflow_dispatch` now. See the new
  "Footgun, already hit once" bullet in AGENTS.md's "Versioning"
  section for the full writeup - read that before touching either
  workflow file.
- README's CI/CD section and AGENTS.md were both updated in the same
  branch to describe this new shape, per the "Keeping the README in
  sync" rule (a `.github/workflows/` file changed meaningfully, so the
  README update happens in the same PR, not a follow-up).

## The effort log (git notes on refs/notes/effort)
- Fully documented in AGENTS.md's "Effort log" section - read that
  before touching it, it's detailed and the details matter.
- Numbers are intentionally not duplicated in this file - they drift
  fast and this file would just go stale again. Query
  `refs/notes/effort` directly, or check the README/PR description,
  which are the actual sources of truth for current standing.
- Always chain `git notes add` and its `git push` into one command,
  never two separate steps - see AGENTS.md for why (a real data-loss
  incident earlier in this project's history).
- The `.git/config` push/fetch refspecs for this ref are local and
  don't survive a fresh clone - AGENTS.md documents a startup check
  for this and the exact commands to paste (agents never run
  `git config` themselves).

## Suggested next step
- Push `feature/fold_publish_build_into_release`, open the PR, and once
  merged, confirm the fix actually works: the *next* `pyproject.toml`
  version bump that reaches `main` should show `release.yml`'s new
  `build` job running right after `tag-and-release` in the Actions tab.
  Nothing has confirmed that yet - this branch is a fix for a bug that
  was found, not yet a proven-working fix.
- If `build` still doesn't run: double-check the `needs.tag-and-release.
  outputs.released` job-output wiring first (an `outputs:` typo or an
  `if:` string-comparison mismatch is the likely culprit) before
  suspecting the `GITHUB_TOKEN` theory needs revisiting.
