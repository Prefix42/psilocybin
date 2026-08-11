"""psilocybin -- induce hallucinations in your codebase, safely.

A fuzz-testing tool for pytest suites. The `Psychonaut` wraps target
callables and, at a configured intensity, hallucinates: mutating
return values or raising unexpected exceptions in their place. The
`TripSitter` enforces guidelines around the trip (duration limits,
hallucination counts, allowed exception types, forbidden targets) and
guarantees the codebase always returns to sobriety when the trip ends.

    from psilocybin import Guidelines, TripSitter

    guidelines = Guidelines(
        seed=42,
        intensity=0.3,
        mode="per_call",   # or "single" for one hallucination per trip
        max_hallucinations=50,
        allowed_exceptions=(ValueError, KeyError),
    )
    sitter = TripSitter(guidelines).guide(["myapp.payments.charge"])

    with sitter:
        run_checkout_flow()

    print(sitter.report.summary())
"""

from .exceptions import BadTripError, GuidelineViolation, PsilocybinError
from .guidelines import Guidelines
from .psychonaut import MODE_PER_CALL, MODE_SINGLE, Psychonaut
from .report import HallucinationEvent, TripReport
from .tripsitter import TripSitter

__all__ = [
    "Guidelines",
    "PsilocybinError",
    "BadTripError",
    "GuidelineViolation",
    "Psychonaut",
    "TripSitter",
    "TripReport",
    "HallucinationEvent",
    "MODE_PER_CALL",
    "MODE_SINGLE",
]

__version__ = "0.1.0"
