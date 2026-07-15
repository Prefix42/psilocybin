# psylocybin

[![CI](https://github.com/Prefix42/psylocybin/actions/workflows/ci.yml/badge.svg)](https://github.com/Prefix42/psylocybin/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/psylocybin.svg)](https://pypi.org/project/psylocybin/)
[![Top Agent](https://img.shields.io/badge/top%20agent-Claude%20Sonnet%205-8A2BE2)](#effort-log)

> **Transparency note:** every line of code, test, and doc in this
> repository was written by AI coding agents, not a human - see the
> [Effort Log](#effort-log) below for exactly who wrote what. A human
> set direction, reviewed the work, and made the calls along the way,
> but never wrote or edited the implementation directly. Part of the
> point of this project is to see how far that division of labor can go.

A hallucination-driven fuzzer for your test suite. `psylocybin` deliberately
makes chosen functions in your codebase lie - mutating return values or
raising unexpected exceptions - so you can see whether the surrounding code
survives it. It's built to plug straight into `pytest`.

Two roles, borrowed from how a psychedelic trip is actually run safely:

- **`Psychonaut`** - takes the trip. It wraps target callables (given as
  dotted import paths) and, at a configured intensity, hallucinates instead
  of behaving normally.
- **`TripSitter`** - watches over the trip. It enforces the `Guidelines` you
  configure (max duration, max hallucination count, which exceptions are
  acceptable, which targets are off-limits), and *guarantees* the codebase
  is restored to normal when the trip ends, whether it ended cleanly or not.

## Install

```bash
pip install psylocybin
```

## Basic usage

```python
from psylocybin import Guidelines, TripSitter

guidelines = Guidelines(
    seed=42,                     # reproducible trip
    intensity=0.3,                # 30% of eligible calls hallucinate
    mode="per_call",               # or "single" -- see "Hallucination modes" below
    max_hallucinations=50,        # bad trip if exceeded
    max_duration_seconds=10,      # bad trip if exceeded
    allowed_exceptions=(ValueError, KeyError),
    forbidden_targets=["myapp.payments.charge_card"],  # never touch this
)

sitter = TripSitter(guidelines).guide(["myapp.inventory.reserve_item"])

with sitter:
    run_checkout_flow()

print(sitter.report.summary())
assert not sitter.report.bad_trip
```

If a guideline is breached - too many hallucinations, the trip ran too long,
or an exception escaped that wasn't on the allowed list - the `with`
block raises `BadTripError` on exit. The target callables are *always*
unpatched first, regardless of outcome, so a bad trip never leaves your
codebase in a hallucinating state.

## pytest integration

Installing the package registers a pytest plugin automatically (via the
`pytest11` entry point). You get a `psylocybin` marker and a `trip_sitter`
fixture for free:

```python
import pytest

@pytest.mark.psylocybin(
    targets=["myapp.orders.place_order"],
    intensity=0.4,
    mode="single",   # one isolated glitch, not sustained flakiness
    seed=1234,
    max_hallucinations=20,
    allowed_exceptions=(ValueError, KeyError),
)
def test_order_flow_survives_hallucination(trip_sitter):
    with trip_sitter:
        run_the_order_flow()
    assert not trip_sitter.report.bad_trip
```

There's also a decorator form if you'd rather not use the marker/fixture:

```python
sitter = TripSitter(Guidelines(intensity=0.5, seed=7))

@sitter.watch(["myapp.orders.place_order"])
def test_order_flow():
    run_the_order_flow()
```

## Hallucination modes

`Guidelines.mode` controls *how many* hallucinations a trip can produce.
`intensity` always means the same thing - the probability that any given
eligible call hallucinates - but what's "eligible" depends on the mode:

- **`"per_call"`** (default) - every call to a target is independently
  eligible for the entire trip. At `intensity=0.3`, roughly 30% of *all*
  calls hallucinate, for as long as the trip runs. Use this to test
  resilience against ongoing, repeated unreliability - e.g. a flaky
  downstream service that misbehaves on and off throughout a whole request.

  ```python
  guidelines = Guidelines(intensity=0.3, mode="per_call", seed=1)
  ```

- **`"single"`** - at most one hallucination happens for the *whole* trip.
  `intensity` is the probability any given call is the one that
  hallucinates; once it's happened, every later call in the trip behaves
  completely normally, no matter the intensity. Use this to test
  resilience against a single, isolated glitch - e.g. one dropped
  connection or one bad response in an otherwise-healthy run.

  ```python
  guidelines = Guidelines(intensity=1.0, mode="single", seed=1)
  # exactly one hallucination will occur somewhere in the trip,
  # guaranteed at intensity=1.0, then it's smooth sailing
  ```

A fresh trip (a new `with sitter:` block after `sitter.guide(...)`) always
starts sober again - `"single"` mode's one-hallucination budget resets
each time a trip begins, it does not carry over across trips.

## What counts as a hallucination

For a given target call selected to hallucinate, `Psychonaut` picks one of:

- **Return mutation** - the real return value is computed, then perturbed
  (booleans flipped, numbers nudged, strings reversed/replaced, collections
  emptied, `None` replaced with a truthy surprise).
- **Exception injection** - a random exception from the configured pool
  (default: `ValueError`, `TypeError`, `RuntimeError`, `KeyError`,
  `IndexError`) is raised instead of the function running at all.

Every induced hallucination is recorded on `TripReport` with the target,
kind, and detail, so a bad trip is fully explainable after the fact.

## Design notes

- Targets are patched with `unittest.mock.patch(..., autospec=True)`, so
  only existing, importable callables can be guided - you can't hallucinate
  something that isn't there.
- `TripSitter.__exit__` unpatches everything *before* evaluating guidelines,
  so a codebase is never left in a "tripping" state, even when a
  `BadTripError` is about to be raised.
- `forbidden_targets` is checked at `guide()` time, before any patching
  happens, so it can't accidentally be bypassed by a bad trip.
- `mode="single"` is enforced inside `Psychonaut` itself (not by
  `TripSitter` aborting after the fact) - once the one hallucination has
  fired, later calls are never even rolled against `intensity`, they just
  behave normally. The one-hallucination budget resets every time a new
  trip starts (`with sitter:`), it isn't shared across separate trips run
  by the same `Psychonaut`/`TripSitter`.

## Development

Install the dev extras and run the same checks CI runs:

```bash
pip install -e ".[dev]"

pytest --cov=psylocybin                       # tests + coverage
ruff check . && ruff format --check .          # lint / style
mypy src                                       # type check
radon cc src -a -s && xenon --max-absolute B --max-modules A --max-average A src  # complexity
bandit -c pyproject.toml -r src                # static security analysis
pip-audit                                      # dependency vulnerability scan
```

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request against `main`:

| Job | Tool | Purpose |
|---|---|---|
| `test` | `pytest` + `pytest-cov` | tests across Python 3.9-3.13, with coverage |
| `lint` | `ruff` | style and lint issues |
| `typecheck` | `mypy` | static type checking |
| `complexity` | `radon` / `xenon` | cyclomatic complexity & maintainability ("code smell") gate |
| `security` | `bandit` + `pip-audit` | static security analysis + dependency CVE scan |
| `secrets` | `gitleaks` | scans the diff/history for committed credentials |

An `all-checks` job aggregates the above into a single required status,
handy as a single branch-protection check.

`.github/workflows/release.yml` tags and publishes a GitHub Release
automatically whenever a push to `main` bumps `pyproject.toml`'s version -
see [AGENTS.md](AGENTS.md#versioning) for the version-bump rule that CI
enforces on every PR to make this possible.

`.github/workflows/publish.yml` builds the sdist/wheel and, once
re-enabled, would publish via
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC,
no long-lived API token stored in the repo):

- Publishing a GitHub **Release** would publish to PyPI.
- `workflow_dispatch` would let you manually target TestPyPI or PyPI.

**The actual PyPI/TestPyPI upload steps are currently disabled**
(`if: false`) while the version-bump/release-automation system above is
still being validated end to end - see
[AGENTS.md](AGENTS.md#versioning). The build/check steps still run, just
nothing gets uploaded yet.

To enable trusted publishing once uploads are turned back on, add a
publisher on both
[pypi.org](https://pypi.org/manage/account/publishing/) and
[test.pypi.org](https://test.pypi.org/manage/account/publishing/) pointing
at this repo, workflow filename (`publish.yml`), and the `pypi` /
`testpypi` GitHub environments referenced in the workflow - no secrets to
configure.

`.github/dependabot.yml` keeps both Python dependencies and the Action
versions themselves patched on a weekly cadence.

## Effort Log

Diff size alone doesn't tell you much - a forty-file find-and-replace
and one obscure, hard-won bug fix can look about the same. To keep
that distinction visible, every commit that represents meaningful
agent work carries a short note on who did it and how deep it was,
via `git notes` on a dedicated ref: `refs/notes/effort`. Current
standing:

| Agent | Running Total |
|---|---|
| Claude Sonnet 5 | 40 commits (10 deep-dive, 23 mechanical, 1 verification, 5 mixed, 1 config) |
| Dependabot (automated) | 5 commits |
| GitHub Copilot | 2 commits (1 deep-dive, 1 mixed) |
| Prefix42 | 1 commit (1 mechanical) |

See [AGENTS.md](AGENTS.md#effort-log) for the full schema, the
`session_scope` category definitions, and the rules for keeping this
honest.
