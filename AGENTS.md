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
  right after making the commit it describes:

  ```bash
  git notes --ref=effort add -F entry.json <commit-sha>
  ```

- Content is strict JSON (no prose notes, so any agent can parse it
  without guessing), with this schema:

  ```json
  {
    "agent": "Claude Sonnet 5",
    "session_scope": "deep-dive | mechanical | verification | mixed | config (see definitions below)",
    "files_touched": 1,
    "summary": "What was actually done, one or two sentences.",
    "verification": "What was run or reproduced to confirm it, if anything.",
    "uncommitted_work": "Optional: related investigation/review in the same session that produced no commit of its own, so it isn't lost just because there's nothing to attach a note to.",
    "self_reported_activity": "Optional, raw and self-reported only (e.g. 'about 12 tool calls'). Not a comparable metric across agents/tools - many agents/humans have no equivalent to report, and a raw count doesn't track with effort or difficulty. Never surface this in the leaderboard's headline columns - see 'MR/PR description: leaderboard' below."
  }
  ```

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

## MR/PR description: leaderboard

When drafting an MR/PR description for this repository (e.g. via the `mr`
skill), append a leaderboard as the LAST section of the description,
built from the effort notes above:

- **This MR/PR**: aggregate `refs/notes/effort` entries for just the
  commits in this MR/PR's range (`git log --notes=effort
  origin/main...HEAD`, or the equivalent base branch) - commit count and
  `session_scope` breakdown, grouped by `agent`.
- **Running total**: the same aggregation, at the same level of detail
  (commit count and `session_scope` breakdown per agent), across the
  entire repository history (`git log --notes=effort --all`) - not a
  bare total count. The leaderboard should show cumulative standing
  across the project at a glance, not just this MR/PR's slice.
- Commits with no effort note still count toward the total - tally them
  as "unscoped" rather than silently excluding them, so the running
  total is never quietly undercounted.
- If `refs/notes/effort` isn't available locally to query (e.g. it was
  never fetched), say so explicitly in the leaderboard section rather
  than omitting it or fabricating numbers.
- Do not include `self_reported_activity` in the leaderboard table. It's
  an optional, non-comparable, self-reported number, not a merit metric -
  putting it in a table cell next to real commit counts would make it
  look like one. If it's worth surfacing at all, do so as a separate,
  clearly-labeled aside below the table, never as a column.

Example shape:

```markdown
## Leaderboard

| Agent | This PR | Running Total |
|---|---|---|
| Claude Sonnet 5 | 4 commits (1 deep-dive, 2 mechanical, 1 mixed) | 12 commits (3 deep-dive, 6 mechanical, 2 verification, 1 mixed) |
| GitHub Copilot | 0 commits | 2 commits (2 mechanical) |
| unscoped | 0 commits | 3 commits (unscoped) |
```

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
