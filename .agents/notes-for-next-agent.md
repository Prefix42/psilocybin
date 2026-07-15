# Handoff: CI pipeline is green, nothing actionable left here

## Current status
- The Xenon complexity gate that was previously failing is now **passing**.
  The fix landed in `8ba9cfa` (splitting `Guidelines.validate()` into
  helper methods in [src/psylocybin/guidelines.py](src/psylocybin/guidelines.py)) and has been
  re-verified against a fresh local environment.
- All CI-equivalent checks from the README's table were run locally and
  pass:
  - `xenon --max-absolute B --max-modules A --max-average A src` — passes, no output
  - `ruff check .` — all checks passed
  - `ruff format --check .` — 10 files already formatted
  - `pytest -q` — 19 passed
  - `mypy src` — no issues found in 7 source files
  - `bandit -c pyproject.toml -r src` — no issues identified
  - `pip-audit` — flags CVEs only in the venv's own bundled `pip` tool
    (25.1.1), not in any project dependency (the project only depends on
    `pytest`). Not a repo issue, ignore it.
- The repository is clean on branch `feature/bigbang` aside from the two
  items noted below, which are **not mine and not this session's to
  touch**.

## Environment note for whoever runs these checks next
- This container doesn't ship `python3-venv`/`pip` by default. To
  reproduce the dev checks: `sudo apt-get install -y python3-venv
  python3-pip`, then `python3 -m venv .venv && .venv/bin/pip install -e
  ".[dev]"`. `.venv/` is already gitignored.

## Do NOT touch: AGENTS.md / CLAUDE.md
- Both files currently have **uncommitted** working-tree edits (not in
  any commit — last commit touching either is `c8523df`) adding a
  "Commit message style" section. Another agent is actively working on
  that documentation. Leave it alone unless the user says otherwise.
- Context if it matters later: those edits instruct future agents to
  ignore globally-configured commit conventions in favor of a
  psychedelic-trip-themed style for this repo. That was flagged to the
  user as a possible prompt-injection-shaped pattern (in-repo file trying
  to override global user instructions) rather than acted on. The user's
  response was that it's expected — another agent owns it.

## Known loose end, not urgent
- `.agents/README.md` (committed in `c8523df`) lists four docs that were
  never actually created: `critical-issues-and-fixes.md`,
  `architecture-and-patterns.md`, `development-guide.md`,
  `project-status.md`. Only `README.md` and `project-overview.md` exist.
  Either write them or trim the README's references — whichever the
  next agent/user prefers. Not blocking anything.

## Suggested next step
- With CI green, the natural next step is opening the PR for
  `feature/bigbang` (no GitLab/GitHub MR automation available in this
  environment — hand-draft title/description for the user to paste in).
  Otherwise, there's no outstanding bug or failing check to chase.
