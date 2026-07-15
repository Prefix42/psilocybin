# Handoff: version-bump enforcement and release automation, on a branch, not yet merged

## Current status
- CI is green, the effort log is live and pushed, README has a
  transparency note and an Effort Log section. All 5 Dependabot
  CI-action bumps (checkout, setup-python, upload-artifact,
  download-artifact, gitleaks-action) are merged.
- **On branch `feature/version_bump_and_release_automation`, not yet
  committed there either as of this writing**: a version-bump
  enforcement CI job, an automatic release/tagging workflow, and
  PyPI/TestPyPI publishing temporarily disabled - see "Versioning" in
  AGENTS.md for the full picture.
- These changes were briefly sitting uncommitted directly on `main`
  before being moved to the branch above - the same mistake happened
  once before in this project's history. Caught both times before
  anything was actually committed to `main`. Worth double-checking
  `git branch --show-current` before committing anything in this repo,
  given the pattern.

## The effort log (git notes on refs/notes/effort)
- Fully documented in AGENTS.md's "Effort log" section - read that
  before touching it, it's detailed and the details matter.
- Survived a real data-loss incident this session: something in this
  environment (likely an IDE's automatic background fetch) repeatedly
  force-updated `refs/notes/effort` to a stale remote state, silently
  destroying locally-added, not-yet-pushed notes. Multiple notes were
  lost and re-added from saved copies before the actual fix was found:
  always chain `git notes add` and its `git push` into one command,
  never two separate steps. That's a hard rule in AGENTS.md now, not a
  suggestion.
- `bookkeeping` is a `session_scope` value for commits whose only
  purpose is re-syncing a displayed leaderboard/badge - these get
  noted (so the overhead is visible) but are excluded from the
  leaderboard's own counts, which is what stops a resync commit from
  immediately making itself stale.
- The `.git/config` push/fetch refspecs for this ref are local and
  don't survive a fresh clone - AGENTS.md documents a startup check
  for this and the exact commands to paste (agents never run
  `git config` themselves).

## README
- Has a "Top Agent" badge and a blockquoted transparency note near the
  top (this project is entirely AI-authored, a human only sets
  direction and reviews), plus an "Effort Log" section at the bottom
  linking to AGENTS.md for the full rules.

## What's new (see "Versioning" in AGENTS.md)
- `pyproject.toml`'s version must now be bumped alongside any `src/`
  change, or any change to `pyproject.toml`'s `dependencies` or
  `requires-python` fields specifically - not the whole file, since
  `dev` extras and tool config never affect what an end user actually
  installs, and a blanket whole-file trigger would block basically
  every routine dependency-bot PR this repo sees (almost all of which
  bump dev tooling, not runtime dependencies). Enforced by a new
  `version-bump` CI job that compares `pyproject.toml`'s version at
  the PR's base SHA vs HEAD, only when one of those triggers fired.
- PR titles must be prefixed `[X.Y.Z]` with whatever version is
  currently in `pyproject.toml` on that branch.
- New `.github/workflows/release.yml`: on push to `main` that touches
  `pyproject.toml`, extracts the version, checks whether a `vX.Y.Z`
  tag already exists (skips if so - handles `pyproject.toml` changing
  for reasons other than a version bump, e.g. a dependency pin), and
  if not, creates the tag and a GitHub Release via `gh release create
  --generate-notes`.
- `publish.yml`'s actual PyPI/TestPyPI publish steps are temporarily
  disabled (`if: false`, original condition preserved as a comment)
  while this is being worked out - creating a release via the above
  will still fire `publish.yml`'s `release: published` trigger, but
  the publish jobs themselves no-op. Don't re-enable without checking
  with the user first - that's their call once they're satisfied with
  the end-to-end flow.

## Known gap, now fixed going forward
- This file went stale for a long stretch this session despite the
  rule to keep it current - "update as soon as status changes" was too
  vague to actually fire in practice. The rule now ties updates to
  concrete checkpoints (drafting a PR description, `AGENTS.md` itself
  changing, end of session as a last resort) instead of a vague
  feeling that something changed - see "Handoff notes" in AGENTS.md.

## Suggested next step
- Commit the pending changes on `feature/version_bump_and_release_automation`
  and open a PR. Once merged, the next real `src/` or runtime-dependency
  change will be the first live test of the version-bump CI check; the
  next `pyproject.toml` version bump will be the first live test of the
  release automation.
