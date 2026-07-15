# Copilot Handoff Notes

This directory contains documentation and handoff notes for collaborative development between agents and contributors.

## Files in this Directory

### project-overview.md
**Project purpose, themes, and core architecture**
- What psylocybin does (hallucination-driven fuzzer)
- Psychedelic metaphor system (Trip, Psychonaut, TripSitter, etc.)
- Core components overview
- Tech stack and use cases

### critical-issues-and-fixes.md
**Reference guide for bugs that were found and how they were fixed**
- 4 HIGH severity issues with code examples
- 5 MEDIUM severity issues (including NaN/infinity edge cases)
- Testing approach and lessons learned
- Important patterns for edge case testing

### architecture-and-patterns.md
**Deep dive into design patterns and how the code is organized**
- Context manager pattern (why patches always restore)
- State management lifecycle
- Hallucination modes (per_call vs single)
- Key invariants to maintain
- Future enhancement points

### development-guide.md
**Practical guide for contributing to the project**
- Quick start commands
- File structure and ownership
- Common development tasks
- Critical code paths to understand
- Debugging tips and pitfalls to avoid

### project-status.md
**Current state, commit history, and test results**
- What's been completed
- Commit history with what was fixed
- Code metrics (19 tests, 100% pass rate)
- Deployment readiness
- How to continue work on different types of tasks

## How to Use This Directory

### For Claude or New Contributors
1. Start with **project-overview.md** to understand what this project does
2. Read **critical-issues-and-fixes.md** to know what pitfalls to avoid
3. Reference **architecture-and-patterns.md** when making design decisions
4. Use **development-guide.md** when adding new features or fixing bugs
5. Check **project-status.md** for current state and next steps

### For Handoff Notes
- Add notes about work completed in the relevant file or create a `NOTES.md` for current session
- Use clear headers with dates if tracking work across sessions
- Include specific file paths and line numbers for bugs/features
- Update project-status.md after significant work

## Current Project State
- ✅ All 19 tests passing
- ✅ 4 HIGH severity issues fixed
- ✅ 5 MEDIUM severity issues fixed  
- ✅ Code review complete
- ✅ Ready for PR or deployment

See **project-status.md** for full details.
