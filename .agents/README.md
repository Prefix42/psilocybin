# Agent Handoff Notes

Shared documentation and handoff notes for agents and contributors working
on psilocybin. Start here, then read the file most relevant to your task.

> Correction (2026-07-15): an earlier version of this index described
> `critical-issues-and-fixes.md`, `architecture-and-patterns.md`,
> `development-guide.md`, and `project-status.md` as complete (e.g. "4 HIGH
> severity issues with code examples") and claimed a code review was done
> and the project was "ready for deployment." Those four files were in fact
> empty placeholders and no such review was recorded. They have now been
> filled in by a real review (see
> [code-review-2026-07-15.md](code-review-2026-07-15.md)), and this index
> reflects what the files actually contain.

## Files in this directory

### project-overview.md
Project purpose, the psychedelic metaphor system (Trip, Psychonaut,
TripSitter, Guidelines, TripReport), core components, tech stack, and use
cases. The quick "what is this."

### design-philosophy.md
The "why": the tool's goal and the project's AI-authorship meta-goal, the
safety-first / metaphor-as-API / reproducibility / defense-in-depth
philosophy, and the meta-process themes (effort log, leaderboard, living
handoff notes). Directly covers goal, design philosophy, and themes.

### architecture-and-patterns.md
The "how": module map, the nested-context-manager and mock/autospec
patterns, where the RNG is spent, the trip state lifecycle, the two
hallucination modes internally, the invariants to maintain, and extension
points.

### critical-issues-and-fixes.md
The review hit list: bugs, fragilities, and design/doc deviations found on
2026-07-15, each with severity, location, evidence, and a recommended fix.
Includes test-coverage gaps. Nothing here has been fixed yet.

### development-guide.md
Practical contributor guide: quick start (and how to bootstrap when
`pip`/`venv` are missing), file structure and ownership, common tasks,
critical code paths, debugging tips, and the pre-PR checklist.

### project-status.md
Evergreen snapshot: verified gate results, what is done, open items, coverage
gaps, and deployment readiness. For the live session-by-session handoff, see
notes-for-next-agent.md instead.

### code-review-2026-07-15.md
The dated record of the review that produced most of the above: scope,
method, and probe evidence.

### notes-for-next-agent.md
The living, session-by-session handoff. Per AGENTS.md this is the source of
truth for where things currently stand; keep it current proactively.

## How to use this directory

1. **project-overview.md** and **design-philosophy.md** - what it is and why.
2. **architecture-and-patterns.md** - how it works, before changing internals.
3. **critical-issues-and-fixes.md** - what is known-broken or fragile, before
   you touch `Psychonaut`/`TripSitter`.
4. **development-guide.md** - setup, tasks, and pitfalls while working.
5. **project-status.md** / **notes-for-next-agent.md** - current state and
   the latest handoff.

Also read [AGENTS.md](../AGENTS.md) for the enforced conventions (versioning,
effort log, commit authorship, PR/leaderboard structure, style).

## For handoff notes

Keep [notes-for-next-agent.md](notes-for-next-agent.md) current - it is the
single living handoff doc (do not start a separate `NOTES.md`). Tie updates
to the checkpoints AGENTS.md lists (drafting a PR, changing AGENTS.md, before
a session ends). Use clear headers, absolute dates, and specific file
paths / line numbers for anything actionable.

## Current project state (2026-07-15)

- [x] Suite green: 19 tests pass; ruff / mypy / bandit / xenon all clean.
- [x] Full review completed and documented (this directory).
- [ ] Open: 1 HIGH (H1 patch-leak) + several MEDIUM/LOW items - see
      [critical-issues-and-fixes.md](critical-issues-and-fixes.md). None
      fixed yet.
- [ ] Not publish-ready by design: uploads disabled, `__version__` stale
      (M1), no `LICENSE` (L5).

See [project-status.md](project-status.md) for the full picture.
