"""pytest integration for psilocybin.

Registered as a pytest11 entry point, so installing the package makes
the `psilocybin` marker and the `trip_sitter` / `psychonaut` fixtures
available automatically -- no need to add anything to conftest.py.

Usage:

    @pytest.mark.psilocybin(
        targets=["myapp.orders.place_order"],
        intensity=0.4,
        mode="per_call",   # or "single" for one hallucination per trip
        seed=1234,
        max_hallucinations=20,
        allowed_exceptions=(ValueError, KeyError),
    )
    def test_order_flow_survives_hallucination(trip_sitter):
        with trip_sitter:
            run_the_order_flow()
        assert not trip_sitter.report.bad_trip
"""

import pytest

from .guidelines import Guidelines
from .tripsitter import TripSitter


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "psilocybin(targets, intensity=0.25, mode='per_call', seed=None, "
        "max_hallucinations=None, max_duration_seconds=None, allowed_exceptions=(), "
        "forbidden_targets=(), halt_on_bad_trip=True): run this test under a "
        "psilocybin hallucination trip. mode is 'per_call' (every call independently "
        "eligible to hallucinate) or 'single' (at most one hallucination for the "
        "whole trip).",
    )


@pytest.fixture
def trip_sitter(request):
    """A TripSitter configured from the closest @pytest.mark.psilocybin, if any."""
    marker = request.node.get_closest_marker("psilocybin")
    kwargs = dict(marker.kwargs) if marker else {}
    targets = kwargs.pop("targets", None)
    if targets is None and marker and marker.args:
        targets = marker.args[0]
    targets = targets or []

    guidelines = Guidelines(**kwargs)
    sitter = TripSitter(guidelines)
    if targets:
        sitter.guide(targets)
    yield sitter


@pytest.fixture
def psychonaut(trip_sitter):
    """The Psychonaut driving the current trip_sitter's session, if configured."""
    return trip_sitter._psychonaut
