"""Psychonaut: the part of psylocybin that actually takes the trip.

A Psychonaut wraps a set of target callables (given as dotted import
paths, e.g. "myapp.billing.charge_card") so that, with some probability
on each call, it hallucinates: it mutates the real return value into
something plausible-but-wrong, or raises an unexpected exception,
instead of behaving normally. This is meant to be used deliberately, as
a fuzzer inside a test suite, to check that surrounding code is
resilient to malformed/unexpected results and exceptions.

A Psychonaut never enforces limits on itself -- that's the TripSitter's
job. The Psychonaut just trips.
"""

import random
from typing import Any, Callable, Iterable, List, Optional
from unittest.mock import patch

from .report import HallucinationEvent, TripReport

DEFAULT_EXCEPTION_POOL = (ValueError, TypeError, RuntimeError, KeyError, IndexError)

#: Every call to a target is independently eligible to hallucinate, at
#: `intensity` probability. This is the default -- good for finding out
#: whether code survives *repeated, ongoing* unreliability.
MODE_PER_CALL = "per_call"

#: At most one hallucination happens for the entire trip. `intensity` is
#: still the probability any given call is the one that hallucinates, but
#: once it's happened, every subsequent call in the trip behaves normally.
#: Good for finding out whether code survives a single, isolated glitch.
MODE_SINGLE = "single"

VALID_MODES = (MODE_PER_CALL, MODE_SINGLE)


class Psychonaut:
    """Induces hallucinations in a set of target callables while active.

    Args:
        targets: dotted import paths to callables to hallucinate, e.g.
            ["myapp.orders.place_order", "myapp.inventory.reserve"].
        intensity: probability (0.0-1.0) that any given eligible call to a
            target hallucinates rather than behaving normally.
        seed: RNG seed for reproducible trips.
        exception_pool: exception classes that may be raised as
            hallucinations. Instantiated with a message when raised.
        report: a TripReport to record events into. If not given, a
            fresh one is created and available as `.report`.
        mode: either "per_call" (each call is independently eligible to
            hallucinate, the default) or "single" (at most one
            hallucination for the whole trip, then every further call
            behaves normally).
    """

    def __init__(
        self,
        targets: Iterable[str],
        intensity: float = 0.25,
        seed: Optional[int] = None,
        exception_pool: Iterable[type] = DEFAULT_EXCEPTION_POOL,
        report: Optional[TripReport] = None,
        mode: str = MODE_PER_CALL,
    ):
        if mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {VALID_MODES}, got {mode!r}")
        self.targets: List[str] = list(targets)
        self.intensity = intensity
        self.exception_pool = tuple(exception_pool)
        self._rng = random.Random(seed)
        self.report = report if report is not None else TripReport()
        self.mode = mode
        self._patchers: List[Any] = []
        self._active = False
        self._hallucinated = False

    def _mutate(self, value: Any) -> Any:
        """Turn a real return value into a plausible hallucination."""
        if isinstance(value, bool):
            return not value
        if isinstance(value, int):
            return value + self._rng.choice([-1, 1])
        if isinstance(value, float):
            return value * self._rng.choice([-1.0, 0.0, 2.0])
        if isinstance(value, str):
            return value[::-1] if value else "\U0001f344"  # mushroom
        if isinstance(value, list):
            return []
        if isinstance(value, tuple):
            return ()
        if isinstance(value, dict):
            return {}
        if value is None:
            return "unexpectedly_not_none"
        return value

    def _wrap(self, target_path: str, original: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not self._active:
                return original(*args, **kwargs)
            if self.mode == MODE_SINGLE and self._hallucinated:
                return original(*args, **kwargs)
            if self._rng.random() >= self.intensity:
                return original(*args, **kwargs)

            self._hallucinated = True
            if self._rng.random() < 0.5:
                result = original(*args, **kwargs)
                mutated = self._mutate(result)
                self.report.record(
                    HallucinationEvent(
                        target=target_path,
                        kind="return_mutation",
                        detail=f"{result!r} -> {mutated!r}",
                    )
                )
                return mutated

            exc_type = self._rng.choice(self.exception_pool)
            self.report.record(
                HallucinationEvent(
                    target=target_path,
                    kind="exception",
                    detail=f"raised {exc_type.__name__}",
                )
            )
            raise exc_type(f"psylocybin hallucination on {target_path}")

        return wrapper

    def __enter__(self) -> "Psychonaut":
        self._active = True
        self._hallucinated = False
        for target_path in self.targets:
            patcher = patch(target_path, autospec=True)
            original = patcher.get_original()[0]
            mock_obj = patcher.start()
            mock_obj.side_effect = self._wrap(target_path, original)
            self._patchers.append(patcher)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._active = False
        for patcher in reversed(self._patchers):
            patcher.stop()
        self._patchers.clear()
