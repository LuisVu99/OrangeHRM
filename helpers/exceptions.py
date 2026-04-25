"""
Custom exceptions for OrangeHRM automation framework.

Provides specific exception types for better error handling and debugging.
"""


class AutomationException(Exception):
    """Base exception class for automation framework."""
    pass


class ElementNotVisibleException(AutomationException):
    """Raised when an expected element is not visible."""
    pass


class ElementNotClickableException(AutomationException):
    """Raised when an element cannot be clicked."""
    pass


class ElementNotFillableException(AutomationException):
    """Raised when an element cannot be filled with text."""
    pass


class TimeoutException(AutomationException):
    """Raised when an operation times out."""
    pass


class NavigationException(AutomationException):
    """Raised when page navigation fails."""
    pass


class AssertionFailedException(AutomationException):
    """Raised when an assertion fails."""
    pass


class FileUploadException(AutomationException):
    """Raised when file upload fails."""
    pass


class ConfigurationException(AutomationException):
    """Raised when configuration is invalid or missing."""
    pass


class TestDataException(AutomationException):
    """Raised when test data generation fails."""
    pass
