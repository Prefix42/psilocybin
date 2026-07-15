# Handoff: CI pipeline still failing

## Current status
- The remaining failing CI gate is the complexity check from Xenon.
- The local failure reproduced with:
  - `xenon --max-absolute B --max-modules A --max-average A src`
- The failing target is the Guidelines class in [src/psylocybin/guidelines.py](src/psylocybin/guidelines.py).

## What was already tried
- I refactored the validation logic in [src/psylocybin/guidelines.py](src/psylocybin/guidelines.py) into smaller helper methods to reduce complexity.
- The change is currently staged in the working tree as a local edit.

## Why this is likely the right fix
- Xenon is flagging the class because its validation method was too complex in one block.
- Splitting validation into focused helper methods preserves behavior while reducing the complexity score.

## What to verify next
1. Run:
   - `ruff check src/psylocybin/guidelines.py`
   - `ruff format --check src/psylocybin/guidelines.py`
   - `pytest -q`
   - `xenon --max-absolute B --max-modules A --max-average A src`
2. If Xenon still fails, inspect whether the new helper methods still push the class/module over the threshold, and consider further splitting or moving validation logic out of the class.

## Important context
- The repository is on branch `feature/bigbang`.
- The current modified file is [src/psylocybin/guidelines.py](src/psylocybin/guidelines.py).
- The earlier full CI-equivalent run showed all other checks passed, including Ruff, mypy, pytest, bandit, and pip-audit.
