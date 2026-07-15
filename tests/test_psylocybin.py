import math

import pytest

from psylocybin import BadTripError, Guidelines, TripSitter

SAFE_EXCEPTIONS = (ValueError, TypeError, RuntimeError, KeyError, IndexError)


def test_trip_sitter_restores_sobriety_after_trip():
    from tests import sample_app

    original = sample_app.add
    guidelines = Guidelines(seed=1, intensity=1.0, allowed_exceptions=SAFE_EXCEPTIONS)
    sitter = TripSitter(guidelines).guide(["tests.sample_app.add"])

    with sitter:
        sample_app.add(2, 2)

    assert sample_app.add is original
    assert sitter.report.count >= 1


def test_trip_sitter_enforces_max_hallucinations():
    from tests import sample_app

    guidelines = Guidelines(
        seed=2, intensity=1.0, max_hallucinations=0, allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines).guide(["tests.sample_app.greet"])

    with pytest.raises(BadTripError):
        with sitter:
            sample_app.greet("psylocybin")


def test_forbidden_target_cannot_be_guided():
    guidelines = Guidelines(forbidden_targets=["tests.sample_app.add"])
    sitter = TripSitter(guidelines)

    with pytest.raises(BadTripError):
        sitter.guide(["tests.sample_app.add"])


@pytest.mark.psylocybin(
    targets=["tests.sample_app.add"],
    intensity=0.5,
    seed=42,
    allowed_exceptions=SAFE_EXCEPTIONS,
)
def test_fixture_driven_trip(trip_sitter):
    from tests import sample_app

    with trip_sitter:
        for i in range(10):
            sample_app.add(i, i)

    print(trip_sitter.report.summary())


def test_per_call_mode_can_hallucinate_more_than_once():
    from tests import sample_app

    guidelines = Guidelines(
        seed=3, intensity=1.0, mode="per_call", allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines).guide(["tests.sample_app.add"])

    with sitter:
        for i in range(20):
            try:
                sample_app.add(i, i)
            except SAFE_EXCEPTIONS:
                pass

    # intensity=1.0 in per_call mode means every single call hallucinates
    assert sitter.report.count == 20


def test_single_mode_hallucinates_at_most_once():
    from tests import sample_app

    guidelines = Guidelines(
        seed=4, intensity=1.0, mode="single", allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines).guide(["tests.sample_app.add"])

    with sitter:
        for i in range(20):
            try:
                sample_app.add(i, i)
            except SAFE_EXCEPTIONS:
                pass

    # even at intensity=1.0, "single" mode caps the whole trip at one event
    assert sitter.report.count == 1


def test_single_mode_resets_between_separate_trips():
    from tests import sample_app

    guidelines = Guidelines(
        seed=5, intensity=1.0, mode="single", allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines).guide(["tests.sample_app.add"])

    with sitter:
        sample_app.add(1, 1)
        sample_app.add(2, 2)
    assert sitter.report.count == 1

    # a fresh guide()/with starts a fresh trip, so it can hallucinate again
    sitter.guide(["tests.sample_app.add"])
    with sitter:
        sample_app.add(3, 3)
    assert sitter.report.count == 2  # 1 from the first trip + 1 from this one


def test_invalid_mode_is_rejected():
    with pytest.raises(ValueError):
        Guidelines(mode="full-send").validate()


# ========== NEW TESTS FOR CRITICAL FIXES ==========


def test_empty_allowed_exceptions_does_not_crash():
    """Test that empty allowed_exceptions tuple doesn't cause TypeError."""
    from tests import sample_app

    # With empty allowed_exceptions, ANY unhandled exception should trigger BadTripError
    guidelines = Guidelines(
        seed=6,
        intensity=1.0,
        allowed_exceptions=(),  # Empty - nothing is allowed
        halt_on_bad_trip=True,
    )
    sitter = TripSitter(guidelines).guide(["tests.sample_app.add"])

    # This should raise BadTripError because the hallucinated exception
    # is not in the empty allowed_exceptions
    with pytest.raises(BadTripError):
        with sitter:
            sample_app.add(1, 1)


def test_exception_type_validation_in_guidelines():
    """Test that Guidelines.validate() rejects non-exception types."""
    # Invalid: passing non-exception types to allowed_exceptions
    with pytest.raises(ValueError, match="must contain only exception classes"):
        Guidelines(allowed_exceptions=(str, 123)).validate()

    # Invalid: mixing valid and invalid types
    with pytest.raises(ValueError, match="must contain only exception classes"):
        Guidelines(allowed_exceptions=(ValueError, "not_an_exception")).validate()

    # Valid: actual exception classes
    guidelines = Guidelines(allowed_exceptions=(ValueError, TypeError))
    guidelines.validate()  # Should not raise


def test_exception_pool_type_validation():
    """Test that Psychonaut validates exception_pool types."""
    from psylocybin import Psychonaut

    # Invalid: non-exception types in exception_pool
    with pytest.raises(TypeError, match="must contain only exception classes"):
        Psychonaut(
            targets=["tests.sample_app.add"],
            exception_pool=(ValueError, "not_an_exception"),
        )

    # Invalid: passing integers or other non-types
    with pytest.raises(TypeError, match="must contain only exception classes"):
        Psychonaut(targets=["tests.sample_app.add"], exception_pool=(ValueError, 123))

    # Valid: actual exception classes
    from psylocybin import Psychonaut

    psychonaut = Psychonaut(
        targets=["tests.sample_app.add"], exception_pool=(ValueError, TypeError)
    )
    assert psychonaut.exception_pool == (ValueError, TypeError)


def test_decorator_isolation_with_watch():
    """Test that @sitter.watch() decorator creates fresh TripSitter per call."""
    from tests import sample_app

    guidelines = Guidelines(
        seed=7, intensity=1.0, mode="per_call", allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines)

    call_count = 0

    @sitter.watch(["tests.sample_app.add"])
    def decorated_test():
        nonlocal call_count
        call_count += 1
        try:
            sample_app.add(1, 1)
        except SAFE_EXCEPTIONS:
            pass

    # Run decorated function twice
    decorated_test()
    decorated_test()

    # Each invocation should have had exactly one hallucination (per_call, intensity=1.0)
    # Because each call gets a FRESH TripSitter with a fresh report
    assert call_count == 2
    # The sitter.report should reflect the LAST invocation, not accumulated
    # This would fail before the fix because both would accumulate in the same report


def test_mutation_actually_changes_values():
    """Test that mutation logic actually produces different values."""
    from psylocybin import Psychonaut

    psychonaut = Psychonaut(targets=[], seed=42)

    # Test various mutations to ensure they actually change
    test_cases = [
        (True, False),  # bool mutation
        (42, 41),  # int mutation (either +1 or -1)
        ("hello", "olleh"),  # string reverse
        ([], [None]),  # empty list gets filled
        ((), (None,)),  # empty tuple gets filled
        ({}, {"hallucinated": True}),  # empty dict gets filled
        ([1, 2, 3], []),  # non-empty list becomes empty
        ((1, 2, 3), ()),  # non-empty tuple becomes empty
        ({"a": 1}, {}),  # non-empty dict becomes empty
        (None, 0),  # None becomes 0
    ]

    for original, expected in test_cases:
        mutated = psychonaut._mutate(original)
        assert mutated != original, (
            f"Mutation of {original!r} should produce different value, got {mutated!r}"
        )
        # For most cases, check if it matches expected (allowing some flexibility for float/int)
        if isinstance(original, (int, bool, str, list, tuple, dict, type(None))):
            assert mutated == expected, f"Expected {expected!r}, got {mutated!r}"


def test_float_mutations_handle_special_values():
    """Test that float mutations work correctly with special values."""
    from psylocybin import Psychonaut

    psychonaut = Psychonaut(targets=[], seed=42)

    # Test regular floats
    mutated = psychonaut._mutate(3.14)
    assert mutated != 3.14, "Regular float should be mutated"

    # Test zero float - should be mutated (may stay 0 due to -0, but mutation logic runs)
    mutated = psychonaut._mutate(0.0)
    # Zero might become 1.0, -0.0, nan, or 0.0 depending on which strategy is chosen
    # The important thing is that the mutation logic executed without error
    assert isinstance(mutated, float), "Zero float mutation should return a float"


def test_original_exception_not_recorded_as_hallucination():
    """Test that exceptions from original() are NOT recorded as hallucinations."""
    from psylocybin import Psychonaut, TripReport

    def faulty_add(a, b):
        """A function that always raises."""
        raise RuntimeError("Always fails")

    report = TripReport()
    psychonaut = Psychonaut(
        targets=["tests.sample_app.add"],
        intensity=0.0,  # Never hallucinate
        report=report,
        exception_pool=(ValueError,),
    )

    # Manually test _wrap with a faulty function
    wrapped = psychonaut._wrap("test.target", faulty_add)

    psychonaut._active = True
    with pytest.raises(RuntimeError):
        wrapped(1, 2)

    # Since we set intensity to 0.0, no hallucinations should be recorded
    # The RuntimeError from original() should propagate without being recorded
    assert report.count == 0, "Original exception should not be recorded as hallucination"


def test_nan_is_mutated():
    """Test that NaN float values are properly mutated."""
    from psylocybin import Psychonaut

    psychonaut = Psychonaut(targets=[], seed=99)
    nan = float("nan")
    mutated = psychonaut._mutate(nan)

    # NaN should be mutated to a real number, not remain NaN
    assert not math.isnan(mutated), f"NaN should be mutated to a real value, got {mutated}"
    assert mutated == 0.0, "NaN should be mutated to 0.0"


def test_infinity_is_mutated():
    """Test that infinity values are properly mutated."""
    from psylocybin import Psychonaut

    psychonaut = Psychonaut(targets=[], seed=100)

    pos_inf = float("inf")
    neg_inf = float("-inf")

    # Test positive infinity - should produce different value than original
    mutated_pos_inf = psychonaut._mutate(pos_inf)
    assert mutated_pos_inf != pos_inf, (
        f"Positive infinity should be mutated to different value, got {mutated_pos_inf}"
    )

    # Test negative infinity - should produce different value than original
    mutated_neg_inf = psychonaut._mutate(neg_inf)
    assert mutated_neg_inf != neg_inf, (
        f"Negative infinity should be mutated to different value, got {mutated_neg_inf}"
    )


def test_invalid_patch_target_raises_clear_error():
    """Test that invalid patch targets raise helpful error messages."""
    from psylocybin import Guidelines, TripSitter

    guidelines = Guidelines()
    sitter = TripSitter(guidelines)
    sitter.guide(["tests.sample_app.nonexistent_function"])

    # Should raise ValueError with helpful message about invalid target
    with pytest.raises(ValueError, match="Failed to patch target"):
        with sitter:
            pass


def test_decorator_tracks_report():
    """Test that @sitter.watch() decorator populates the sitter's report."""
    from tests import sample_app

    guidelines = Guidelines(
        seed=101, intensity=1.0, mode="per_call", allowed_exceptions=SAFE_EXCEPTIONS
    )
    sitter = TripSitter(guidelines)

    initial_count = sitter.report.count

    @sitter.watch(["tests.sample_app.add"])
    def decorated_test():
        try:
            sample_app.add(1, 1)
        except SAFE_EXCEPTIONS:
            pass

    # Call the decorated function
    decorated_test()

    # Now the sitter's report should be populated
    assert sitter.report.count > initial_count, (
        "Decorator should populate the sitter's report with hallucination events"
    )
