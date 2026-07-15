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
