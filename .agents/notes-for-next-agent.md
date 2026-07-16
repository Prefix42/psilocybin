# Handoff: full review done - suite green, but real open issues found

## Latest session (2026-07-15): documentation review + hit list

A full project review was completed (no code changed - documentation only).
See [code-review-2026-07-15.md](code-review-2026-07-15.md) for scope/method
and [critical-issues-and-fixes.md](critical-issues-and-fixes.md) for the full
hit list. Key updates to the picture below:

- **The suite is green, not broken.** Verified locally on Python 3.13:
  `pytest` 19/19, `ruff`/`mypy`/`bandit` clean, `xenon` passes, `radon` avg
  A. The prior framing of "assume nothing works" did not hold empirically.
- **But there are real open issues** the passing tests do not cover. The
  headline is **H1**: `Psychonaut.__enter__`
  ([psychonaut.py L180-L196](../src/psylocybin/psychonaut.py#L180-L196)) is
  not atomic - on a multi-target trip where a later target is invalid, the
  earlier targets stay patched and keep actively hallucinating for the rest
  of the process (reproduced). This violates the project's core "always
  return to sobriety" promise and has no test. It is the top fix.
- Other confirmed items: `__version__` drift (0.1.0 vs pyproject 0.1.2, M1),
  infinity-mutation no-op that only passes by seed luck (M2), a seed-fragile
  test (M3), plus a batch of LOW polish/doc items. Full detail + recommended
  fixes in the hit list.
- **Docs were out of sync:** `.agents/`'s `critical-issues-and-fixes.md`,
  `architecture-and-patterns.md`, `development-guide.md`, and
  `project-status.md` were empty placeholders that `.agents/README.md`
  described as complete. They are now filled in, a new `design-philosophy.md`
  and this review record were added, and the README index was corrected.
- **Nothing here is fixed yet.** A future session that picks up H1 (or any
  `src/` change) must add the missing regression test, bump the version (CI
  requires it), author commits as the agent+model, and add an effort note.
- **`AGENTS.md` gained a handoff-notes pruning rule** this session (under
  "Handoff notes"): prune entries as they resolve, and collapse this file to
  a short all-clear when nothing is outstanding. Noted here per AGENTS.md's
  own "whenever AGENTS.md changes" handoff checkpoint.

The release-automation history below is still accurate and worth reading
before touching the workflows - it just is no longer the whole story.

## Environment toolchain gap - ACTION: prompt the user to install these

This environment ships almost none of the tooling the project's own
documented workflow needs. **At the start of every session, check once
whether the toolchain is present (e.g. `command -v pip uv pytest`), and if it
still is not, remind the user of this gap regardless of the session's task**
- do not wait until you are about to run something, and do not gate the
reminder on doing dev work. This is a standing, once-per-session reminder
until it is handled. The only reason to check first is so this stops once it
is done: if the tools already resolve, the user has taken care of it - prune
this section per the handoff-notes pruning rule in `AGENTS.md` (drop whichever
tools now resolve; delete the section outright once nothing here is
outstanding) and move on. Otherwise, surface it and offer to have the tools
installed, so no one has to re-bootstrap by hand like the 2026-07-15 review
did.

What is actually present: `python3` (3.13 only), `git`, `jq`, `curl`,
`wget`. That is it.

What the 2026-07-15 review needed and had to bootstrap by hand: there is
**no `pip`, no `venv`/`ensurepip`, no `uv`, no `pipx`, no `virtualenv`**. The
workaround was to `curl` `get-pip.py`, `python3 get-pip.py --target <dir>`,
then `pip install --target <dir> ...` with `PYTHONPATH`/`PATH` pointed at it
(see [development-guide.md](development-guide.md) for the exact incantation
and its gotchas). It works, but it is slow and fiddly and re-derived from
scratch each session.

### Blocking essentials (needed to run the documented dev/CI workflow)

Ask the user to have these added to the environment so the
[development-guide.md](development-guide.md) Quick start just works:

- A working `pip` + `venv`/`ensurepip` (the `python3.13-venv` /
  `python3-pip` system packages), **or** `uv` (a single static binary that
  provides install + venv + resolver and would sidestep the whole
  bootstrap - the cleanest single ask).
- The `[dev]` extras the project already declares: `pytest`, `pytest-cov`,
  `ruff`, `mypy`, `bandit`, `pip-audit`, `radon`, `xenon`, `build`. With a
  working pip, `pip install -e ".[dev]"` covers these; listing them here so
  the user knows the full set.
- `twine` (used by the build/release workflows for `twine check`; not in the
  `[dev]` extras but exercised by CI).

### Christmas list (not needed this pass, but would genuinely help here)

Rationale tied to this specific repo's conventions, not generic wishlist:

- **Python 3.9, 3.10, 3.11, 3.12** interpreters. Only 3.13 is present, but CI
  tests the full 3.9-3.13 matrix and the package floor is 3.9. Without the
  older interpreters a local run cannot catch a 3.9-only break (directly
  relevant to L11, the mypy-targets-3.10-vs-floor-3.9 finding), and cannot
  reproduce a matrix-specific CI failure.
- **`tox` or `nox`** - to drive that multi-version matrix locally instead of
  one interpreter at a time.
- **`gh` (GitHub CLI)** - this repo is GitHub-hosted with heavy release
  automation; `release.yml` itself shells out to `gh release create`. `gh`
  would let an agent inspect workflow runs, releases, and PR state directly
  instead of guessing.
- **`act`** - runs GitHub Actions workflows locally. Given how much of this
  project's history is release/CI-workflow debugging (and the documented
  `GITHUB_TOKEN` anti-recursion footgun), being able to dry-run a workflow
  change before pushing would be high-value.
- **`gitleaks`** - the exact secret-scanner CI runs (the `secrets` job).
  Having it locally lets an agent reproduce that gate before pushing.
- **`git` with a usable notes setup** - `git` is present, but the effort-log
  convention lives on `refs/notes/effort` with local-only push/fetch
  refspecs that do not survive a fresh clone (see the effort-log section
  below). `jq` is already here, which is enough to parse the strict-JSON
  effort notes; just flagging that the notes refspecs are part of the
  environment setup, not just the tools.

When you raise this, offer the user the single-biggest-win framing: adding
`uv` plus the four missing Python interpreters would unblock essentially
everything above in two installs.

## Release-automation status (still current)
- The release/publish pipeline is now fully proven, not just wired up:
  - PR #8 added `release.yml` (tag + GitHub Release on a `pyproject.toml`
    version bump) and a `version-bump` CI gate, with PyPI/TestPyPI
    publishing left disabled.
  - PR #9 smoke-tested it (0.1.0 -> 0.1.1) and confirmed tagging/release
    creation worked, but that test also surfaced a real bug: the release
    it created never triggered `publish.yml`'s `release: published`
    trigger, because `release.yml` creates the release with the
    automatic `secrets.GITHUB_TOKEN`, and GitHub deliberately blocks
    `GITHUB_TOKEN`-triggered events from starting other workflow runs
    (anti-recursion safeguard). Even `publish.yml`'s harmless
    `build`/`twine check` job had never actually run.
  - PR #10 fixed it by moving the build/`twine check` step directly into
    `release.yml` as a `build` job gated on `needs.tag-and-release.
    outputs.released == 'true'`, and dropped `publish.yml`'s dead
    `release: published` trigger (now manual-`workflow_dispatch`-only).
    It also included a deliberate patch bump (0.1.1 -> 0.1.2) to prove
    the fix on merge - **confirmed working by the user**: the `build`
    job actually fired this time. Tag `v0.1.2` exists on the merge
    commit.
  - See AGENTS.md's "Versioning" section, specifically the "Footgun,
    already hit once" bullet, for the full writeup - read that before
    touching `release.yml` or `publish.yml` again, so this bug doesn't
    get reintroduced.
- The actual PyPI/TestPyPI upload steps in `publish.yml` are still
  disabled (`if: false`) - that's an intentional, separate decision from
  the build-job fix above, and re-enabling them is the user's call.

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
- The README's Effort Log table needed two separate resync commits
  during PR #10 (`session_scope: bookkeeping` each time) because new
  commits kept landing on the branch after the first sync - a live
  example of the "Keeping the README in sync" rule in AGENTS.md
  actually being applied, not just documented.

## Known gap: no CI enforcement behind either convention
- Early in this project's history, the user asked for a CI check to
  verify the effort log was being kept current, so "a smelly human
  can't forget it either." As far as the commit history shows, that was
  never actually built - only the AGENTS.md conventions exist (the
  effort-log schema, the "Keeping the README in sync" rule, the
  handoff-notes checkpoints), with no automated check backing any of
  them. This isn't a deliberate decision recorded anywhere, it looks
  like it simply never got done - worth surfacing rather than assuming
  either it was rejected on purpose or that it already exists.
- If this gets picked up: verifying `refs/notes/effort` state in CI is
  genuinely harder than the other checks in `ci.yml`, since notes live
  on a separate ref (`refs/notes/effort`) that isn't fetched by a
  default `actions/checkout` - it would need an explicit fetch of that
  ref first, plus a decision about how strict to be (every commit
  needs a note? only non-bookkeeping ones? what about Dependabot's
  commits, which never get one by design?). Verifying
  `notes-for-next-agent.md` was "meaningfully" updated is fuzzier still
  - a CI check can confirm the file changed, not that the update was
  honest.

## Suggested next step
- No known open issue right now - the release pipeline works end to
  end, from a version bump landing on `main` through tag, GitHub
  Release, and distribution build. The next natural trigger for
  project work is whatever the user brings, or - if it ever comes up -
  deciding whether to re-enable the actual PyPI/TestPyPI upload steps
  in `publish.yml`, which remains the user's call to make, not an
  agent's to assume. The CI-enforcement gap above is also fair game if
  the user wants to revisit it.
