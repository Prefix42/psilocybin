# Handoff: sober, CI green, docs squared away

## Current status
- The Xenon complexity gate is fixed and stays fixed. The structural
  change from `8ba9cfa` (splitting `Guidelines.validate()` into helper
  methods in [src/psylocybin/guidelines.py](src/psylocybin/guidelines.py)) is untouched by everything
  since - later commits only straightened dashes in its docstring.
- Full CI-equivalent check suite passes on the current tree:
  - `xenon --max-absolute B --max-modules A --max-average A src` - passes, no output
  - `ruff check .` - all checks passed
  - `ruff format --check .` - 10 files already formatted
  - `pytest -q` - 19 passed
  - `mypy src` - no issues found in 7 source files
  - `bandit -c pyproject.toml -r src` - no issues identified
  - `pip-audit` - flags CVEs only in the venv's own bundled `pip` tool,
    not any project dependency (project only depends on `pytest`). Not a
    repo issue, ignore it.
- Branch `feature/bigbang` is clean, nothing outstanding.

## Environment note for whoever runs these checks next
- This container doesn't ship `python3-venv`/`pip` by default. To
  reproduce the dev checks: `sudo apt-get install -y python3-venv
  python3-pip`, then `python3 -m venv .venv && .venv/bin/pip install -e
  ".[dev]"`. `.venv/` is already gitignored.

## AGENTS.md is now the canonical instructions file
- `CLAUDE.md` just points at `AGENTS.md` now (`620221e`) - read `AGENTS.md`
  directly.
- `AGENTS.md` establishes repo-local conventions that deliberately
  override globally-configured agent conventions, confirmed intentional
  by the user - this repo is a special case, not an oversight to correct:
  - No emoji, no em/en dashes anywhere (source, docs, commit messages).
  - Commit messages lean into the project's psychedelic-trip theme and
    terminology instead of any global commit-message-format convention.
  - Commits made by an AI agent are authored/committed as that specific
    agent and model (e.g. `Claude Sonnet 5 <claude-sonnet-5@anthropic.com>`),
    set per-commit rather than via git config, overriding any global
    guidance toward a generic non-model-specific identity.
- Apply these when making commits in this repo. Do not "fix" them back
  toward generic/global conventions.

## Doc loose end from the previous handoff: resolved
- `.agents/architecture-and-patterns.md`, `critical-issues-and-fixes.md`,
  `development-guide.md`, and `project-status.md` (referenced by
  `.agents/README.md` but previously missing) now exist as honest
  placeholders pointing back to this file for live, current handoff
  info, rather than fabricated content. `README.md`'s CI badge was also
  fixed to point at the real repo (`Prefix42/psylocybin`, not the
  placeholder `OWNER/psylocybin`).

## Suggested next step
- With CI green and docs squared away, the natural next step is opening
  the PR for `feature/bigbang` (no GitLab/GitHub MR automation available
  in this environment - hand-draft title/description for the user to
  paste in). Otherwise, there's no outstanding bug or failing check to
  chase.
