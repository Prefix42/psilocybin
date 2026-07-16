# psylocybin Repository Overview

## Purpose
A hallucination-driven fuzzer for Python test suites. Deliberately mutates return values or raises unexpected exceptions in target functions to verify surrounding code handles failures gracefully.

## Core Themes & Metaphors
The project uses **psychedelic culture metaphors** consistently throughout:
- **Trip**: A fuzzing/testing session
- **Hallucination**: A mutation or injection of chaos (wrong return values or exceptions)
- **Psychonaut**: Component that induces hallucinations (wraps target callables)
- **TripSitter**: Component that enforces boundaries/guidelines (guarantees safe recovery)
- **Bad Trip**: When guidelines are violated (too many hallucinations, timeout, unexpected exceptions)
- **Intensity**: Probability (0.0-1.0) that any eligible call hallucinates

## Key Components
1. **Psychonaut** - Takes the trip; wraps target callables and makes them misbehave at configured intensity
2. **TripSitter** - Watches over the trip; enforces Guidelines and guarantees codebase recovery
3. **Guidelines** - Configuration: seed, intensity, mode, max_hallucinations, max_duration_seconds, allowed_exceptions, forbidden_targets
4. **TripReport** - Records hallucination events and trip statistics

## Hallucination Modes
- **per_call** (default): Every call independently eligible to hallucinate (tests ongoing/repeated failures)
- **single**: At most one hallucination per entire trip (tests single isolated glitch)

## Tech Stack
- Python 3.9+
- pytest integration via plugin entry point
- Uses unittest.mock.patch for function wrapping
- Includes decorators and fixtures for test integration

## Use Cases
- Testing resilience to flaky services
- Verifying error handling in critical paths
- Ensuring code gracefully degrades under failure

## Related notes
- [design-philosophy.md](design-philosophy.md) - the goal, philosophy, and themes behind these choices.
- [architecture-and-patterns.md](architecture-and-patterns.md) - how the components fit together internally.
- [critical-issues-and-fixes.md](critical-issues-and-fixes.md) - known bugs and design deviations (hit list).
- [project-status.md](project-status.md) - current verified state.
