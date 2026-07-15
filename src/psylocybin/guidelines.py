"""Guidelines: the configured boundaries a trip must stay within."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Optional

from .psychonaut import MODE_PER_CALL, VALID_MODES


@dataclass
class Guidelines:
    """Configuration enforced by a TripSitter over a Psychonaut's session.

    Attributes:
        seed: RNG seed for reproducible trips. None means non-deterministic.
        intensity: probability (0.0-1.0) that any given eligible call
            hallucinates. What counts as "eligible" depends on `mode`.
        mode: "per_call" (default) — every call to a target is
            independently eligible to hallucinate, at `intensity`
            probability, for the whole trip. Good for testing resilience
            to ongoing/repeated unreliability.
            "single" — at most one hallucination happens for the entire
            trip; `intensity` is the probability any given call is the
            one that hallucinates, and once it has, every later call in
            the trip behaves normally. Good for testing resilience to a
            single, isolated glitch.
        max_hallucinations: abort the trip if more than this many
            hallucinations are induced. None means unlimited. (With
            mode="single" this is naturally capped at 1 already; this
            setting is mainly useful with mode="per_call".)
        max_duration_seconds: abort the trip if it runs longer than this.
            None means unlimited.
        allowed_exceptions: exception types a hallucination is permitted to
            raise (and that are permitted to escape the `with sitter:` block)
            without being treated as a bad trip.
        forbidden_targets: dotted paths that must never be hallucinated,
            even if requested — guiding one raises GuidelineViolation.
        halt_on_bad_trip: if True, a guideline breach raises BadTripError.
            If False, the breach is only recorded on the TripReport.
    """

    seed: Optional[int] = None
    intensity: float = 0.25
    mode: str = MODE_PER_CALL
    max_hallucinations: Optional[int] = None
    max_duration_seconds: Optional[float] = None
    allowed_exceptions: Sequence[type[BaseException]] = field(default_factory=tuple)
    forbidden_targets: Sequence[str] = field(default_factory=tuple)
    halt_on_bad_trip: bool = True

    def validate(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        if self.mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {VALID_MODES}, got {self.mode!r}")
        if self.max_hallucinations is not None and self.max_hallucinations < 0:
            raise ValueError("max_hallucinations must be >= 0")
        if self.max_duration_seconds is not None and self.max_duration_seconds <= 0:
            raise ValueError("max_duration_seconds must be > 0")

        # Validate that allowed_exceptions contains only exception classes
        for exc in self.allowed_exceptions:
            if not isinstance(exc, type) or not issubclass(exc, BaseException):
                raise ValueError(
                    f"allowed_exceptions must contain only exception classes, got {exc!r}"
                )
