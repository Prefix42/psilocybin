"""Exceptions raised by psylocybin."""


class PsylocybinError(Exception):
    """Base error for the psylocybin package."""


class BadTripError(PsylocybinError):
    """Raised when a hallucination session exceeds its configured guidelines."""


class GuidelineViolation(BadTripError):
    """Raised when a specific guideline boundary is breached, e.g. a
    forbidden target was requested for hallucination."""
