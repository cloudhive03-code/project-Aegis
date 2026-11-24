
class LogParseError(Exception):
    """Raised when a log cannot be parsed."""
    
class InvalidIncidentIdError(ValueError):
    """Raised when an incident ID does not follow the Aegis format."""
    
class NotificationError(Exception):
    """Raised when a notification cannot be delivered."""