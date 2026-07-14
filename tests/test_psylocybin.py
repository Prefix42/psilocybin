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
