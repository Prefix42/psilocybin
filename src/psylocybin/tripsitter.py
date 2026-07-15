"""TripSitter: watches over a Psychonaut and keeps the trip safe.

The TripSitter is responsible for:
  * checking requested targets against `forbidden_targets` before the
    trip starts;
  * making sure the codebase always returns to sobriety -- patched
    callables are unpatched -- even if the trip ends in an unhandled
    exception;
  * enforcing `max_hallucinations` / `max_duration_seconds` after the
    trip, and deciding whether it was a "safe landing" or a "bad trip";
  * deciding whether an exception that escaped the trip is acceptable
    (in `allowed_exceptions`) or constitutes a bad trip.
"""

import functools
from collections.abc import Callable, Iterable
from time import monotonic
from typing import Optional

from .exceptions import BadTripError, GuidelineViolation
from .guidelines import Guidelines
from .psychonaut import Psychonaut
from .report import TripReport


class TripSitter:
    """Supervises a single Psychonaut session against a set of Guidelines."""

    def __init__(self, guidelines: Guidelines):
        guidelines.validate()
        self.guidelines = guidelines
        self.report = TripReport()
        self._psychonaut: Optional[Psychonaut] = None

    def _check_target_allowed(self, target: str) -> None:
        for forbidden in self.guidelines.forbidden_targets:
            if target == forbidden or target.startswith(forbidden + "."):
                raise GuidelineViolation(
                    f"target '{target}' is forbidden by guidelines and cannot be guided"
                )

    def guide(self, targets: Iterable[str]) -> "TripSitter":
        """Configure which callables the psychonaut will hallucinate on."""
        targets = list(targets)
        for t in targets:
            self._check_target_allowed(t)
        self._psychonaut = Psychonaut(
            targets=targets,
            intensity=self.guidelines.intensity,
            seed=self.guidelines.seed,
            report=self.report,
            mode=self.guidelines.mode,
        )
        return self

    def __enter__(self) -> "TripSitter":
        if self._psychonaut is None:
            raise BadTripError("no psychonaut configured -- call .guide(targets) first")
        self.report.started_at = monotonic()
        self._psychonaut.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Always bring the codebase back to sobriety first, no matter what.
        if self._psychonaut is None:
            self.report.ended_at = monotonic()
            return False

        self._psychonaut.__exit__(exc_type, exc, tb)
        self.report.ended_at = monotonic()

        reason = self._evaluate(exc_type, exc)
        if reason:
            self.report.bad_trip = True
            self.report.bad_trip_reason = reason
            if self.guidelines.halt_on_bad_trip:
                raise BadTripError(reason) from exc
            # Not halting: swallow an escaping exception since it's
            # already captured in the report as the bad-trip reason.
            return exc_type is not None

        # No violation. If an exception escaped but is on the allowed
        # list, suppress it -- that's an expected hallucination side
        # effect, not a test failure.
        allowed = tuple(self.guidelines.allowed_exceptions or ())
        if allowed and exc_type is not None and issubclass(exc_type, allowed):
            return True
        return False

    def _evaluate(self, exc_type, exc) -> str:
        g = self.guidelines
        if g.max_duration_seconds is not None and self.report.duration > g.max_duration_seconds:
            return (
                f"trip exceeded max_duration_seconds "
                f"({self.report.duration:.3f}s > {g.max_duration_seconds}s)"
            )
        if g.max_hallucinations is not None and self.report.count > g.max_hallucinations:
            return (
                f"trip exceeded max_hallucinations ({self.report.count} > {g.max_hallucinations})"
            )
        allowed = tuple(g.allowed_exceptions or ())
        if exc_type is not None and (not allowed or not issubclass(exc_type, allowed)):
            return f"unguided exception escaped the trip: {exc_type.__name__}: {exc}"
        return ""

    def watch(self, targets: Iterable[str]) -> Callable:
        """Decorator form.

        @sitter.watch(["myapp.orders.place_order"])
        def test_order_flow_survives_hallucination():
            ...

        Note: Each decorated function invocation resets the TripSitter's state
        to ensure proper test isolation. The sitter's report will reflect only
        the most recent invocation.
        """
        targets = list(targets)

        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                # Reset state for test isolation
                self._psychonaut = None
                self.report = TripReport()
                # Guide and execute
                self.guide(targets)
                with self:
                    return fn(*args, **kwargs)

            return wrapped

        return decorator
