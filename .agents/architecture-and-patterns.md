# Architecture and Patterns

*Placeholder - not yet written. See `.agents/README.md` for how this fits
into the rest of the handoff docs.*

## Intended use

A deep dive into the design patterns used in this codebase and how the
code is organized, covering:

- The context manager pattern (why patches always restore)
- State management lifecycle across a trip
- The two hallucination modes (`per_call` vs `single`) and how they differ
  internally
- Key invariants to maintain when touching `Psychonaut`/`TripSitter`
- Future enhancement points
