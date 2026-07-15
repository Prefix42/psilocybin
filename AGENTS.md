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
Update it as soon as status actually changes - a fix lands, CI goes green
or red, a loose end gets resolved, a new one appears - rather than
batching it all up at the end. Treat it as the living source of truth
for where things currently stand, not a one-time handoff memo.

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

  ```bash
  git notes --ref=effort add -F entry.json <commit-sha>
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
  `git push origin refs/notes/effort:refs/notes/effort`. This is a
  deliberate choice to avoid silently changing anyone's git config;
  run these manually (or ask the user before an agent pushes).
- **Known footgun, confirmed in practice, not hypothetical**: if the
  configured fetch refspec for this ref starts with `+` (force update -
  `+refs/notes/effort:refs/notes/effort`), any fetch - including an
  IDE's automatic background fetch, not just a deliberate one - will
  silently overwrite the local ref with whatever's on the remote,
  destroying any local notes added since the last push, with zero
  warning. This already happened once in this repo's history: a note
  written locally was silently lost to a background fetch before it
  had been pushed, and had to be re-added from a saved copy. Two
  mitigations, not mutually exclusive:
  - Don't leave a note unpushed for long - push soon after adding one,
    since the vulnerable window is exactly "local note exists, hasn't
    been pushed yet."
  - Prefer a fetch refspec *without* the leading `+`
    (`refs/notes/effort:refs/notes/effort`). Without force, a fetch
    that would overwrite local-only notes fails loudly instead
    (`[rejected] ... (non-fast-forward)`) rather than silently
    discarding them - forcing a deliberate `git notes --ref=effort
    merge` to reconcile, instead of losing data no one noticed was at
    risk. This is a git config change, so an agent can recommend it but
    never make it - see the config-check bullet above.
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

## PR description: leaderboard

When drafting a PR description for this repository - this repo is
hosted on GitHub, so "PR" throughout, never "MR" - append a leaderboard
as the LAST section of the description, built from the effort notes
above:

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
| Ada Lovelace | 0 commits | 1 commit (1 config) |
```

(`Ada Lovelace` above illustrates the "list everyone, even at 0 This PR"
rule - included because Running Total is nonzero, sorted last because
it's the smallest.)

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
