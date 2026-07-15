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
        
        # Validate exception_pool contains only exception classes
        exception_pool_tuple = tuple(exception_pool)
        for exc in exception_pool_tuple:
            if not isinstance(exc, type) or not issubclass(exc, BaseException):
                raise TypeError(
                    f"exception_pool must contain only exception classes, "
                    f"got {exc!r}"
                )
        
        self.targets: List[str] = list(targets)
        self.intensity = intensity
        self.exception_pool = exception_pool_tuple
        self._rng = random.Random(seed)
        self.report = report if report is not None else TripReport()
        self.mode = mode
        self._patchers: List[Any] = []
        self._active = False
        self._hallucinated = False

    def _mutate(self, value: Any) -> Any:
        """Turn a real return value into a plausible hallucination."""
        import math
        
        if isinstance(value, bool):
            # Special case bool before int check since bool is subclass of int
            return not value
        if isinstance(value, int):
            # Add or subtract 1, ensuring mutation
            delta = self._rng.choice([-1, 1])
            return value + delta
        if isinstance(value, float):
            # Handle special float values
            if math.isnan(value):
                # NaN is never equal to anything (including itself), so return different value
                return 0.0
            # For floats, try different mutation strategies
            # These strategies are ordered to ensure most produce mutations
            choice = self._rng.choice([0, 1, 2, 3])
            if choice == 0:
                # Negate - works for everything including inf
                return -value
            elif choice == 1:
                # Invert - always produces different value (0->1, fin->fin, inf->0)
                if value == 0:
                    return 1.0
                else:
                    return 1.0 / value
            elif choice == 2:
                # Add for finite, negate for infinite
                if math.isinf(value):
                    return -value
                else:
                    return value + self._rng.choice([-1.0, 1.0])
            else:
                # Multiply by values that are never 1.0
                multiplier = self._rng.choice([0.5, 2.0, -1.0, 0.0])
                # 0.0 * anything = 0.0, which is different from non-zero
                # -1.0 * x = -x, which is different from x
                # 0.5 * x and 2.0 * x are different from x for most values
                return value * multiplier
        if isinstance(value, str):
            # Reverse for non-empty, return a fixed mutation for empty
            return value[::-1] if value else "HALLUCINATED"
        if isinstance(value, list):
            # Return empty list if non-empty, otherwise return a list with a dummy
            return [] if value else [None]
        if isinstance(value, tuple):
            # Return empty tuple if non-empty, otherwise return a tuple with a dummy
            return () if value else (None,)
        if isinstance(value, dict):
            # Return empty dict if non-empty, otherwise return a dict with a dummy
            return {} if value else {"hallucinated": True}
        if value is None:
            # For None, use a falsy sentinel value that is distinct from None
            # Use 0 which is falsy like None but a different type
            return 0
        # For unknown types, try to return something different
        # Return the type name as a marker that mutation happened
        return f"<hallucinated {type(value).__name__}>"

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
                try:
                    result = original(*args, **kwargs)
                except Exception:
                    # If original() raises, that's a real exception, not a hallucination.
                    # Let it propagate without recording it as a hallucination.
                    raise
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
            try:
                patcher = patch(target_path, autospec=True)
                original = patcher.get_original()[0]
            except (AttributeError, ImportError, TypeError) as e:
                raise ValueError(
                    f"Failed to patch target '{target_path}': {type(e).__name__}: {e}. "
                    f"Target must be a valid importable path to a callable, e.g. 'mymodule.function'"
                )
            mock_obj = patcher.start()
            mock_obj.side_effect = self._wrap(target_path, original)
            self._patchers.append(patcher)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._active = False
        for patcher in reversed(self._patchers):
            patcher.stop()
        self._patchers.clear()
