# Goal, Design Philosophy, and Themes

Written 2026-07-15 from a full read of the code, docs, `AGENTS.md`, and
commit history. This is the "why" companion to
[project-overview.md](project-overview.md) (the "what") and
[architecture-and-patterns.md](architecture-and-patterns.md) (the "how").

## The goal

psilocybin is a **hallucination-driven fuzzer for test suites**. Instead of
fuzzing inputs, it fuzzes the *behavior of your own functions*: at a
configured probability it makes chosen callables lie - returning a
plausible-but-wrong value, or raising an unexpected exception - so you can
find out whether the surrounding code survives when a dependency
misbehaves. It plugs into `pytest` so this can live inside an existing
suite.

There are really two goals stacked on top of each other:

1. **The tool's goal:** exercise a codebase's resilience to unreliable
   collaborators (flaky services, functions that occasionally return
   garbage), with reproducible, bounded, always-recoverable fault injection.
2. **The project's meta-goal:** it is an explicit experiment in how far
   AI-agent-authored software can be pushed. Per the README transparency
   note, every line of code, test, and doc was written by AI coding agents;
   a human set direction and reviewed, but never wrote implementation
   directly. Much of the surrounding machinery (the effort log, the
   versioning discipline, the handoff notes) exists to study and sustain
   that division of labor.

## Design philosophy

### Safety first, and safety by construction

The dominant value in the design is that **the tool must never leave your
codebase broken**, even when a trip goes wrong. This shows up as concrete,
structural choices rather than best-effort cleanup:

- Cleanup happens *before* judgment: `TripSitter.__exit__` unpatches
  everything and only then decides whether the trip was "bad" and whether to
  raise. A bad verdict never coexists with a still-patched codebase.
- The guardrail that matters most (`forbidden_targets`) is enforced at
  `guide()` time, before any patching, so it cannot be bypassed by a trip
  that has already gone sideways.
- Limits are the supervisor's job, not the tripper's: `Psychonaut` never
  enforces anything on itself (the one exception, `single`-mode's budget,
  is a behavioral rule, not a safety limit); `TripSitter` owns duration,
  count, allowed-exception, and forbidden-target enforcement.

The current implementation mostly lives up to this, with one real gap: a
setup-phase failure can leak patches (H1 in
[critical-issues-and-fixes.md](critical-issues-and-fixes.md)). That gap is
notable precisely *because* it violates the project's headline promise -
it's the highest-value thing to fix.

### The metaphor is the API, and it is disciplined

The psychedelic-trip metaphor is not decoration bolted onto a normal API -
it *is* the vocabulary of the public surface, and it is used with unusual
consistency:

- **Psychonaut** takes the trip (induces hallucinations).
- **TripSitter** watches over it (enforces guidelines, guarantees a safe
  landing).
- **Guidelines** are the boundaries agreed before the trip.
- **Trip / hallucination / bad trip / intensity / safe landing / sobriety**
  all map cleanly onto real testing concepts (session / injected fault /
  guideline breach / probability / clean exit / unpatched state).

The metaphor also carries real semantic weight: the two roles enforce a
genuine separation of concerns (inducer vs supervisor), and "the sitter
guarantees you come back" is both the theme and the core invariant.
`AGENTS.md` deliberately extends this into commit messages ("lean into the
trip theme"), so the theme is a maintained convention, not an accident.

The package was originally shipped under a misspelled name, "psylocybin"
(with a `y`), instead of the actual mushroom compound "psilocybin". It has
since been renamed throughout the code, tests, and packaging to the correct
spelling - if you see "psylocybin" anywhere outside old commit history or
this note, it's a leftover that should be fixed, not an intentional
stylization.

### Reproducibility, bounded blast radius, defense in depth

- **Reproducible by seed:** a `seed` makes a whole trip deterministic. The
  caveat (documented in
  [architecture-and-patterns.md](architecture-and-patterns.md)) is that a
  single shared RNG stream means reproducibility is scoped to one code
  version, not stable across changes to mutation logic.
- **Bounded:** `intensity`, `max_hallucinations`, `max_duration_seconds`,
  and the `single` vs `per_call` modes all exist to control how much chaos a
  trip can produce, so the fault injection is a dial, not an on/off switch.
- **Defense in depth:** `autospec=True` means you cannot hallucinate a
  callable that isn't there or call it with the wrong signature; validation
  lives in both `Guidelines.validate()` and `Psychonaut.__init__`;
  forbidden-target checks pre-empt patching.

### Engineered like a "real" library, on purpose

Despite being an experiment, the project deliberately holds itself to a
production bar, which is part of the point (can agents sustain that bar?):

- A broad CI matrix (Python 3.9-3.13) plus gates for lint (`ruff`), types
  (`mypy`), complexity (`radon`/`xenon`), security (`bandit`, `pip-audit`),
  and secrets (`gitleaks`), aggregated behind a single `all-checks` status.
- Release automation that tags and builds on a version bump, with a
  hard-won understanding of a `GITHUB_TOKEN` anti-recursion footgun baked
  into both the workflows and `AGENTS.md`.
- Dependabot on both pip and Actions.

As of this review the code clears all of those gates (see
[project-status.md](project-status.md)).

## The meta-process themes (unique to this repo)

These are conventions, documented in `AGENTS.md`, that exist to make the
AI-authorship experiment legible over time:

- **The effort log** (`git notes` on `refs/notes/effort`): a per-commit,
  strict-JSON record of *who* did the work and *how deep* it was
  (deep-dive / mechanical / verification / config / mixed / bookkeeping),
  because a diff's size doesn't reveal its difficulty. It even tracks its
  own overhead (the `bookkeeping` scope) and survived a real, documented
  data-loss incident that shaped its "always chain add+push" rule.
- **A leaderboard** in the README and PR descriptions, aggregating those
  notes into per-agent standings.
- **Living handoff notes** ([notes-for-next-agent.md](notes-for-next-agent.md))
  tied to concrete checkpoints (drafting a PR, changing `AGENTS.md`) because
  a vague "keep it updated" demonstrably didn't fire.
- **A recurring lesson:** every one of these conventions started as "just
  remember to do X", drifted, and was re-anchored to an event that already
  happens. The repo has learned, repeatedly, that unattached good intentions
  don't survive - and that lesson is itself now part of the design.

## What this means for a contributor

- Preserve the safety invariants and the metaphor; both are load-bearing,
  not cosmetic.
- Expect to re-baseline seeded tests when you touch mutation/RNG code, and
  say so.
- Keep `pyproject.toml`'s version, the effort log, the README leaderboard,
  and the handoff notes in sync per `AGENTS.md` - the process discipline is
  as much "the project" as the code is.
- Read [critical-issues-and-fixes.md](critical-issues-and-fixes.md) before
  changing `Psychonaut`/`TripSitter`: the open items there are exactly the
  places where the current code falls short of the philosophy above.
