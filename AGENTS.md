# Agent Repository Instructions

Before making changes to this repository, review the shared project notes in the .agents directory.

## Required context
- Read .agents/README.md first.
- Then review the relevant docs in .agents/:
  - project-overview.md
  - critical-issues-and-fixes.md
  - architecture-and-patterns.md
  - development-guide.md
  - project-status.md

## Expectations
- Use these files as the primary source of project context, constraints, and current status.
- Follow the documented architecture and patterns rather than inventing new approaches.
- If a task is ambiguous, consult the shared notes before proposing or implementing changes.

## Handoff notes

Keep [.agents/notes-for-next-agent.md](.agents/notes-for-next-agent.md)
accurate proactively, not just as a final step before a session ends.

"Update it as soon as status actually changes" turned out to be too
vague to actually happen in practice - an entire session's worth of
work (a whole subsystem built, a real data-loss incident survived,
several CI fixes) went by without a single update, because there was
no concrete moment that triggered it. Tie it to checkpoints that
already happen instead of a vague feeling that "status changed":

- Whenever drafting or regenerating a PR description for this repo.
- Whenever `AGENTS.md` itself changes - a process/convention shift is
  exactly the kind of thing this file exists to record.
- At minimum, once before a session ends - but treat that as the last
  resort, not the only trigger.

Treat it as the living source of truth for where things currently
stand, not a one-time handoff memo.

**Prune it: the notes are a transfer, not an archive.** This file exists to
carry forward what the next session still needs - not to accumulate a running
log of everything that was ever true. Keep it lean by removing entries as
they stop being actionable, in the same session you resolve them:

- When an item is done, or its durable content now lives in a permanent doc
  (e.g. `.agents/project-status.md`,
  `.agents/critical-issues-and-fixes.md`,
  `.agents/architecture-and-patterns.md`), delete it from the handoff notes.
  If the fact is worth keeping, make sure it is captured in that permanent
  doc first - the handoff file points at the durable docs, it does not
  duplicate them.
- Prune at the granularity of what actually resolved. If an entry or section
  lists several things and only some are handled, remove those and leave the
  rest - do not clear a whole section because part of it is done, and do not
  keep a whole section alive because one item lingers.
- When nothing is left outstanding, the file should say exactly that. A short
  all-clear - e.g. "Nothing to hand off; current state is in
  `.agents/project-status.md` and the rest of `.agents/`" - is the correct
  resting state, not a pile of stale, already-done entries. A handoff file
  with no open actions is a success, not a gap to fill in.

Rule of thumb: if an entry describes something already true and stable, it
belongs in a permanent doc; if it describes something the next agent must
still do, decide, or watch, it belongs here - and only until it is handled.

## Effort log

Commit diffs alone don't distinguish a mechanical sweep (e.g. a
find-and-replace touching forty files) from a deep, hard-won investigation
(e.g. chasing one obscure race condition). To keep that distinction
visible over time, agents record a short effort note for their own work
using `git notes`, on a dedicated ref kept separate from any other notes
usage:

- Ref: `refs/notes/effort` (always pass `--ref=effort` explicitly - do not
  use the default notes ref).
- One note per commit that represents meaningful agent work. Add it
  right after making the commit it describes. Never note a merge
  commit - merges are excluded from every query below via
  `--no-merges` and aren't "work" in the sense this log tracks, so a
  note on one would just be dead weight.
- **Always chain the add and the push into one command, never two
  separate steps** - see the footgun below for why this is not
  optional:

  ```bash
  git notes --ref=effort add -F entry.json <commit-sha> && \
    git push origin refs/notes/effort:refs/notes/effort
  ```

- Content is strict JSON (no prose notes, so any agent can parse it
  without guessing), with this schema:

  ```json
  {
    "agent": "Claude Sonnet 5",
    "session_scope": "deep-dive | mechanical | verification | mixed | config | bookkeeping (see definitions below)",
    "files_touched": 1,
    "summary": "What was actually done, one or two sentences.",
    "verification": "What was run or reproduced to confirm it, if anything.",
    "uncommitted_work": "Optional: related investigation/review in the same session that produced no commit of its own, so it isn't lost just because there's nothing to attach a note to.",
    "self_reported_activity": "Optional, raw and self-reported only (e.g. 'about 12 tool calls'). Not a comparable metric across agents/tools - many agents/humans have no equivalent to report, and a raw count doesn't track with effort or difficulty. Never surface this in the leaderboard's headline columns - see 'PR description: leaderboard' below.",
    "confidence": "self | estimated. 'self' means the agent named in `agent` wrote this note about its own work, at the time. 'estimated' means a different agent inferred it after the fact from the diff/commit message alone, with no session context - even a delayed self-backfill by the same agent name counts as 'self' only if it's genuinely recalling the work, not reconstructing it from the diff. Required whenever confidence isn't 'self'.",
    "estimated_by": "Required when confidence is 'estimated': who made the estimate. Omit entirely when confidence is 'self'."
  }
  ```

  Every note ever written to this repo's `refs/notes/effort` so far is
  itself only a rough estimate, self-reported or not - treat `confidence`
  as a hedge on top of an already-fuzzy signal, not a claim that `self`
  notes are precise and `estimated` ones aren't.

- `session_scope` definitions, kept intentionally loose - this is a rough
  trend signal, not a precise taxonomy:
  - `deep-dive`: the work was investigative - forming and testing
    hypotheses, reproducing a bug, chasing something non-obvious - even
    if the resulting diff is small.
  - `mechanical`: broad, low-judgment changes - formatting, find/replace,
    applying an already-understood fix pattern across many files.
  - `verification`: confirming already-done work still holds - rerunning
    checks, re-deriving state - without new investigation or a
    functional change.
  - `config`: a contained infrastructure/tooling change (CI, permissions,
    dependency pins) where the change itself is small and well-understood
    once found, even if some diagnosis preceded it.
  - `mixed`: genuinely spans more than one of the above within a single
    commit's work.
  - `bookkeeping`: work that exists purely to keep this leaderboard/log
    itself in sync with reality - updating a README/PR leaderboard
    table or the top-agent badge to reflect already-recorded commits,
    with no other project change bundled in. Still gets a note, so the
    overhead of maintaining this system is itself a visible metric, but
    see "PR description: leaderboard" below for why it's excluded
    from the counts.
  - If a commit's work doesn't cleanly fit one category, use `mixed`
    rather than deliberating over it - don't spend more effort
    classifying the work than the work itself took.
- If related work in the same session also produced a commit, fold a
  short description of the uncommitted part into that commit's
  `uncommitted_work` field - concretely, whatever commit is HEAD at the
  time you write the note, not necessarily whichever commit came right
  before or after the work chronologically.
- If the session produced no commit at all (a pure review, an audit that
  changed nothing), there is nothing to attach a note to, and borrowing
  an unrelated pre-existing commit - possibly another agent's, from an
  earlier session - would misattribute the work. Instead, create an
  empty anchor commit for it, authored/committed as the agent per the
  convention above, and attach the note to that:

  ```bash
  git commit --allow-empty -m "..."
  git notes --ref=effort add -F entry.json HEAD
  ```

- To read effort notes: `git log --notes=effort --format='%H%n%N'` (or
  `git notes --ref=effort show <sha>` for one commit). Prefer asking an
  agent to pull and summarize these rather than reading raw JSON by hand.
- The `effort` ref is not fetched or pushed by default - it lives on a
  separate ref that plain `git fetch`/`git push` ignore. To sync it
  explicitly: `git fetch origin refs/notes/effort:refs/notes/effort` /
  `git push origin refs/notes/effort:refs/notes/effort`.
- **Pushing `refs/notes/effort` is an explicit exception to the usual "ask
  the user before an agent pushes" rule - an agent may push it freely,
  without asking first.** This ref is the effort log's own dedicated ref,
  holding nothing but effort notes, and each agent maintains its own entries
  on it - so adding a note and chaining its push (per the footgun rule
  below) is the intended, self-service workflow and needs no separate
  approval. Keep the exception narrow: it covers pushing `refs/notes/effort`
  and nothing else. Pushing any other ref (a branch, a tag, a different
  notes ref) still follows the normal rule of asking the user first. It also
  does not extend to `git config`: setting up or fixing the push/fetch
  refspec stays the user's to run, since agents never run `git config`
  themselves (see the startup check below).
- **Known footgun, confirmed in practice, not hypothetical, and it took
  real effort to pin down**: something in this environment (most likely
  an IDE's automatic background fetch) periodically force-updates
  `refs/notes/effort` to match the remote, silently destroying any
  local notes added since the last push, with zero warning. This
  happened repeatedly in this repo's history within a single session -
  multiple notes were silently lost before being pushed, each time
  re-added from a saved copy.
  - The first suspected cause was the fetch refspec's leading `+`
    (force update - `+refs/notes/effort:refs/notes/effort`). Removing
    it did **not** stop the clobbering - the loss kept the exact same
    signature (always reverting to the same stale remote commit)
    afterward, meaning whatever is fetching is very likely forcing the
    update at the command level (e.g. `git fetch --force`), which
    overrides the refspec's own `+`/no-`+` setting regardless of local
    config. Prefer a fetch refspec without the leading `+` anyway as
    harmless defense in depth, but do not treat it as sufficient on its
    own - it demonstrably wasn't.
  - The actual defense: **always chain the note add and the push into
    one command** (see above), never add a note and leave it for a
    later, separate push. A forced sync can only destroy local-only
    (unpushed) notes - once local matches remote, a forced sync is a
    no-op, not a loss. This doesn't reduce the *probability* of a
    clobber, it eliminates the *window* it can act on, which is what
    actually matters here.
  - If notes keep going missing even with chaining (e.g. a clobber
    lands in the gap between the `add` and the `push` themselves, not
    just after), that means chaining isn't sufficient and this approach
    needs to be escalated, in order: first reconsider a tracked
    `worklog.md`-style file instead of `git notes` (committing the
    entry atomically with the work it describes removes the gap
    entirely, at the cost of needing its own commit approval rather
    than git notes' lighter-touch add); if that's still not robust
    enough, look outside git entirely for where this data lives.
- **Footgun, confirmed in practice:** if a commit gets rewritten after its
  note was added (an `--amend`, or a cherry-pick-then-amend used to fix
  authorship - see the rebase footgun in "Commit authorship" above), the
  note stays attached to the *old* SHA unless you explicitly move it. It's
  easy to add the note to whatever SHA `git commit`/`git cherry-pick` just
  printed and move on, without noticing a later amend changed the SHA out
  from under it - the note silently ends up orphaned on a commit reachable
  from no branch, while the real (final) commit has none. After any
  amend/rebase of a noted commit, verify with
  `git notes --ref=effort show <final-sha>` that the note landed on the
  SHA actually reachable from a branch, not an intermediate one.
- At the start of a session in this repo, check once (not per command)
  whether the refs/notes/effort push/fetch refspecs are set up, by
  reading `.git/config` directly (not `git config`, which requires
  approval) and looking for these lines under `[remote "origin"]`:

  ```
  push = refs/notes/effort:refs/notes/effort
  fetch = refs/notes/effort:refs/notes/effort
  ```

  This is local, uncommitted config, so it does not survive a fresh
  clone. If either line is missing, tell the user and offer the exact
  command to paste - agents never run `git config` themselves, even
  with approval. If the fetch line has a leading `+`
  (`+refs/notes/effort:refs/notes/effort`), flag it - see the footgun
  above - and offer the command to fix it, same rule: recommend, never
  run it yourself.

## Keeping the README in sync

The README's Effort Log table and Top Agent badge, and its CI/CD section,
have gone stale before - drifting for several merged PRs (including a
handful of Dependabot merges never reflected as a leaderboard row) before
anyone noticed. "Keep it in sync" without a concrete trigger didn't work
for handoff notes either (see above) for the same reason: a vague
ongoing obligation with no specific moment attached to it just doesn't
fire. Tie README updates to checkpoints that already happen:

- Whenever a PR description is drafted or regenerated (see "PR
  description: structure and leaderboard" below) and its Running Total
  differs from what's currently in the README's Effort Log table -
  update the table (and the Top Agent badge, if the top agent changed)
  in that same PR, not a follow-up. The badge's `logo` query param (a
  shields.io/simple-icons slug, e.g. `claude`) names an icon for the
  specific top agent, not just a color - if the new top agent is a
  different product or vendor, swap the slug to match (e.g.
  `githubcopilot` for GitHub Copilot) rather than leaving the old badge's
  icon under a new label.
- Whenever a workflow file under `.github/workflows/` is added, removed,
  or has its trigger/behavior meaningfully changed (e.g. a job disabled
  or re-enabled) - update the CI/CD section in the same PR, so the
  README never describes a pipeline that doesn't match what's actually
  wired up.
- Before opening any PR, do a quick sanity check: does this PR's
  Running Total, or anything in `.github/workflows/`, disagree with
  what the README currently says? If so, fold the fix into the PR
  rather than leaving it for someone to notice later.

A README-only sync with no other project change bundled in is
`session_scope: bookkeeping` - see the Effort log section above for why
that's still noted but excluded from the leaderboard counts.

## Versioning

`pyproject.toml`'s `version` field must be bumped in the same PR as any
change under `src/`, or any change to `pyproject.toml`'s `dependencies`
or `requires-python` fields specifically - not the whole file. This is
enforced by CI (the `version-bump` job in `.github/workflows/ci.yml`),
which fails the PR otherwise - not a suggestion, a blocking check.

- Deliberately scoped narrower than "any `pyproject.toml` change":
  `dev` extras (ruff, mypy, bandit, etc.) and tool config
  (`[tool.ruff]`, `[tool.mypy]`, and the like) never affect what
  `pip install psilocybin` actually installs for an end user, so they
  don't require a bump - and just as importantly, a blanket whole-file
  trigger would block every routine dependency-bot PR in this repo,
  since almost all of its traffic here is dev-tooling bumps, not
  runtime dependencies.
- Bump policy (patch/minor/major) is left to judgment - this repo
  doesn't have a formal semver policy yet, just the requirement that
  *some* bump happens alongside a triggering change.
- PR titles must be prefixed `[X.Y.Z]` only when that PR itself bumps
  `pyproject.toml`'s version - e.g. `[1.0.0] Fix the mutation strategy
  for negative zero`, using the new version being introduced. A PR that
  doesn't touch the version gets no prefix at all - it marks the PR
  that changed the version, not a running label for whatever version
  happens to be current.
- Merging a PR that changes `pyproject.toml`'s version triggers
  `.github/workflows/release.yml`, which tags and creates a GitHub
  Release automatically - see that workflow for exactly how it decides
  whether a release is actually warranted (it's not just "did the file
  change").
- The actual PyPI/TestPyPI publish steps in `publish.yml` are
  **temporarily disabled** (`if: false`, with the original condition
  left as a comment) while this version-bump/release-automation system
  is still being worked out. Don't silently re-enable them - that's the
  user's call once they're satisfied with how this works end to end.
- **Footgun, already hit once:** `release.yml` creates its GitHub
  Release using the automatic `secrets.GITHUB_TOKEN`. GitHub
  deliberately does not let events triggered by `GITHUB_TOKEN` start
  other workflow runs (an anti-recursion safeguard) - so a `release:
  types: [published]` trigger anywhere else in this repo will never
  actually fire off the back of it, even though the release genuinely
  gets created. `publish.yml` used to rely on exactly that trigger and
  it silently never ran (not even its harmless `build` job) until this
  was noticed and fixed. The fix in place now: `release.yml` builds and
  `twine check`s the distribution itself, as a `build` job that runs
  right after `tag-and-release` (gated on `needs.tag-and-release.outputs.
  released == 'true'`, so it only runs when a release was actually
  created, not when `pyproject.toml` changed without a version bump).
  `publish.yml` no longer listens for `release: published` at all - it's
  reachable only by manual `workflow_dispatch`. Don't reintroduce a
  `release: published` trigger expecting it to fire automatically off
  `release.yml`'s own release - it won't, unless the token used to
  create that release changes (e.g. a PAT instead of `GITHUB_TOKEN`,
  which has its own tradeoffs and hasn't been adopted here).

## PR description: structure and leaderboard

When drafting a PR description for this repository - this repo is
hosted on GitHub, so "PR" throughout, never "MR" - structure it as:

Drafting or regenerating a PR description is also one of the triggers
(see "Handoff notes" above) for reviewing
[.agents/notes-for-next-agent.md](.agents/notes-for-next-agent.md) itself
- what's changed, what can be closed off, what needs to be noted for the
next session. Do that review before or after drafting the title/body,
whichever fits the flow better - just don't let generating the
description substitute for it, since the description and the handoff
notes serve different readers (this PR's reviewer vs. the next session).

- `## Overview` - a short intro paragraph, what this PR does and why.
- `## What changed` - the substance, broken into `###` subsections per
  area touched (e.g. one per workflow file, one for docs). This is the
  user's confirmed preference over a flat list of `###` sections with
  no enclosing headers - the two-level structure reads better.
- The leaderboard (below), appended as the LAST section.

Building the leaderboard itself, from the effort notes above:

- **This PR**: aggregate `refs/notes/effort` entries for just the
  commits in this PR's range (`git log --no-merges --notes=effort
  origin/main...HEAD`, or the equivalent base branch) - commit count and
  `session_scope` breakdown, grouped by `agent`.
- **Running total**: the same aggregation, at the same level of detail
  (commit count and `session_scope` breakdown per agent), across
  `git log --no-merges --notes=effort origin/main HEAD` - not a bare
  total count. Always pass `--no-merges`: merge commits aren't agent
  work and are never noted (see the Effort log section above), so
  counting them would only ever inflate "unscoped" with noise. This is
  a union of two specific refs (everything reachable from the real
  trunk, `origin/main`, or from this PR's own branch), not `--branches`
  and not `--all`:
  - `--all` walks `refs/notes/effort` itself (each `git notes add`
    creates a commit on that ref), polluting the count with the notes
    ref's own internal plumbing commits rather than real project work -
    not to be confused with the `bookkeeping` session_scope below,
    which is a different thing on the *project's* own history.
  - `--branches` walks *every* local branch indiscriminately. If work
    happened on some other branch that was abandoned and never merged
    into `origin/main`, `--branches` would still count it forever as
    long as that stale branch ref exists locally - `origin/main HEAD`
    only ever counts the real trunk plus the specific branch being
    described, so abandoned work that never shipped is never counted.
  - Use `origin/main`, not local `main`: local `main` can itself be
    stale if nobody's pulled recently, silently undercounting.
  - The leaderboard should show cumulative standing across the project
    at a glance, not just this PR's slice - once this PR merges,
    `origin/main`'s own history will include it, so this number is a
    preview of the post-merge total, not a separate, disconnected
    figure.
- List every agent that has ever contributed (i.e. appears anywhere in
  the Running Total column), even if their This PR count is 0 -
  don't drop a row just because someone didn't touch this particular
  PR. Sort rows by Running Total, descending (highest cumulative
  contribution first).
- Commits with no effort note still count toward the total - tally them
  as "unscoped" rather than silently excluding them, so the running
  total is never quietly undercounted.
- Commits authored by `dependabot[bot]` - author email containing
  `49699333+dependabot[bot]@users.noreply.github.com`, Dependabot's
  fixed GitHub App user ID, consistent across every repo, not just this
  one - never have an effort note and never will, since Dependabot
  doesn't participate in this convention. Give these their own row,
  labeled `Dependabot (automated)`, rather than folding them into
  "unscoped" - they're a known, identifiable source, not a genuine gap
  in the log the way an unscoped human/agent commit would be. Still
  sorted into the table by Running Total like any other row, per the
  sort rule above.
- Exclude commits noted `session_scope: bookkeeping` from every count
  and breakdown entirely - not "unscoped", not counted under any
  agent, just left out, as if they were never in the log at all. This
  is deliberate, not an oversight: a bookkeeping commit's entire
  purpose is re-syncing the leaderboard to match already-recorded work,
  so counting it would immediately make the number it just wrote stale
  again, needing another sync, forever. Leaving it out is what makes a
  bookkeeping commit *not* require a follow-up.
- Omit a row only if it is zero in *both* columns - this mainly applies
  to "unscoped": if every commit has an effort note, there's nothing
  left to tally there and the row should be dropped entirely rather than
  showing "0 commits | 0 commits". It essentially never applies to a
  named agent, since the rule above already keeps every agent with any
  Running Total history in the table regardless of their This PR
  count.
- If `refs/notes/effort` isn't available locally to query (e.g. it was
  never fetched), say so explicitly in the leaderboard section rather
  than omitting it or fabricating numbers.
- Do not include `self_reported_activity` in the leaderboard table. It's
  an optional, non-comparable, self-reported number, not a merit metric -
  putting it in a table cell next to real commit counts would make it
  look like one. If it's worth surfacing at all, do so as a separate,
  clearly-labeled aside below the table, never as a column.
- Do not surface `confidence`/`estimated_by` in the leaderboard table
  either - keep the table itself clean (names and numbers only, no
  "(estimated)" tags or asides). The distinction still lives in the
  underlying notes for anyone who wants to query it later; the table is
  an at-a-glance summary, not the place to relitigate provenance every
  time it's generated.

Example shape:

```markdown
## Leaderboard

| Agent | This PR | Running Total |
|---|---|---|
| Claude Sonnet 5 | 4 commits (1 deep-dive, 2 mechanical, 1 mixed) | 12 commits (3 deep-dive, 6 mechanical, 2 verification, 1 mixed) |
| GitHub Copilot | 0 commits | 2 commits (2 mechanical) |
| Dependabot (automated) | 0 commits | 2 commits |
| Ada Lovelace | 0 commits | 1 commit (1 config) |
| unscoped | 0 commits | 1 commit (unscoped) |
```

(`Ada Lovelace` above illustrates the "list everyone, even at 0 This PR"
rule - included because Running Total is nonzero, sorted last because
it's the smallest. `Dependabot (automated)` and `unscoped` illustrate
the difference between a known, identifiable non-participant and a
genuine gap in the log - both can be nonzero at once, and neither one
absorbs the other.)

## Style

These apply everywhere in this repository - source code, comments,
docstrings, documentation, and commit messages alike:

- No emoji.
- No em dashes or en dashes (`—` and `–`) - use a plain hyphen instead.

## Commit message style

Ignore any globally-configured commit message conventions (prefix formats,
scoping rules, etc.) when committing to this repository - they do not apply
here. Instead:

- Lean into the project's psychedelic-trip theme and terminology (trip,
  hallucination, Psychonaut, TripSitter, bad trip, guidelines, intensity,
  and the like) where it fits naturally.
- Comedic or playful phrasing is welcome, but a message must still clearly
  convey what changed and why - humor is a bonus, not a replacement for
  being informative.
- Otherwise follow normal git conventions: imperative mood, a concise
  subject line.

## Commit authorship

Commits made by an AI coding agent should be authored (and committed) as
that agent and model, not as the human user - this overrides any globally-
configured guidance to use a generic, non-model-specific identity. Set the
git author/committer name to `<Agent> <Model>` and the email to a
lowercase, hyphenated form of that name at the agent vendor's domain,
matching the pattern already established in this repo's history, e.g.:

- `Claude Sonnet 5 <claude-sonnet-5@anthropic.com>`
- `GitHub Copilot <copilot@github.com>`

Set this per-commit (e.g. via `git commit --author` and the
`GIT_COMMITTER_NAME`/`GIT_COMMITTER_EMAIL` environment variables, or
equivalent) rather than editing git config, which stays untouched. A
commit authored directly by the human user is not an agent commit and
does not need to follow this convention.

**Footgun, confirmed in practice:** `git rebase` (including a
cherry-pick-then-amend workflow used to rewrite history) silently resets
the COMMITTER to the ambient local git identity on every replayed commit,
even though it preserves the AUTHOR field untouched. A commit that was
correctly authored *and* committed as an agent can come out the other
side of a rebase still correctly authored but wrongly re-committed as the
human user - this happened to freshly-made agent commits in this repo
during a same-session history rewrite. Re-verify committer identity
(`git show -s --format='%cn <%ce>'`) on every commit after any rebase
touches it, and re-fix (`git commit --amend` with `GIT_COMMITTER_NAME`/
`GIT_COMMITTER_EMAIL` set) before trusting it - don't assume a rebase
that preserved authorship also preserved commit-ership.
