"""Exceptions raised by psilocybin."""


class PsilocybinError(Exception):
    """Base error for the psilocybin package."""


class BadTripError(PsilocybinError):
    """Raised when a hallucination session exceeds its configured guidelines."""


class GuidelineViolation(BadTripError):
    """Raised when a specific guideline boundary is breached, e.g. a
    forbidden target was requested for hallucination."""
