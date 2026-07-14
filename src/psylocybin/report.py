"""Records of what happened during a trip."""

from dataclasses import dataclass, field
from time import monotonic
from typing import List, Optional


@dataclass
class HallucinationEvent:
    """A single induced hallucination."""

    target: str
    kind: str  # "return_mutation" | "exception"
    detail: str
    timestamp: float = field(default_factory=monotonic)


@dataclass
class TripReport:
    """Summary of a Psychonaut's session, as observed by a TripSitter."""

    events: List[HallucinationEvent] = field(default_factory=list)
    started_at: float = field(default_factory=monotonic)
    ended_at: Optional[float] = None
    bad_trip: bool = False
    bad_trip_reason: str = ""

    def record(self, event: HallucinationEvent) -> None:
        self.events.append(event)

    @property
    def duration(self) -> float:
        end = self.ended_at if self.ended_at is not None else monotonic()
        return end - self.started_at

    @property
    def count(self) -> int:
        return len(self.events)

    def summary(self) -> str:
        status = "BAD TRIP" if self.bad_trip else "safe landing"
        lines = [
            f"psylocybin trip report -- {status}",
            f"  hallucinations induced: {self.count}",
            f"  duration: {self.duration:.3f}s",
        ]
        if self.bad_trip:
            lines.append(f"  reason: {self.bad_trip_reason}")
        for e in self.events:
            lines.append(f"   - [{e.kind}] {e.target}: {e.detail}")
        return "\n".join(lines)
