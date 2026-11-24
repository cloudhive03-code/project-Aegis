
from typing import Protocol

from incident import Incident
from models import IncidentIdGap


class Alert(Protocol):
    def send(self, message: str) -> None:
        ...
class GapNotifier(Protocol):
    def notify(self, gap: IncidentIdGap) -> None:
        """
        Notify about an incident ID gap.

        Raises:
            NotificationError: If notification delivery fails.
        """
        ...
        
class EmailAlert:
    def send(self, message: str) -> None:
        print(f"Email: {message}")
class SMSAlert:
    def send(self, message: str) -> None:
        print(f"SMS: {message}")
class AlertService:
    def __init__(self, alert: Alert):
        self.alert = alert
    def notify(self, incident: Incident) -> None:
        message = (
            f"{incident.severity} incident detected! "
            f"ID: {incident.id}, "
            f"User: {incident.user}, "
            f"IP: {incident.ip}, "
            f"Score: {incident.score}, "
            f"Action: {incident.action}"
        )
        self.alert.send(message)
        
class IncidentIdGapNotifier:
    def __init__(self, alert: Alert):
        self.alert = alert

    def notify(self, gap: IncidentIdGap) -> None:
        message = (
            "Aegis detected an unclassified incident ID "
            "sequence anomaly. "
            f"Missing IDs: {', '.join(gap.missing_ids)}. "
            "Investigation recommended."
        )

        self.alert.send(message)