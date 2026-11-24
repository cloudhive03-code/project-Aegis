
from datetime import datetime, timezone
from typing import ClassVar


class Incident:
    severity_scores: ClassVar[dict[str, int]] = {
        "CRITICAL": 10,
        "WARNING": 5,
        "INFO": 1
    }

    def __init__(
        self,
        incident_id: str,
        time: str,
        severity: str,
        user: str,
        ip: str
    ) -> None:
        self.id = incident_id
        self.time = time
        self.severity = severity
        self.user = user
        self.ip = ip

        self.score: int = self.calculate_score()
        self.notes: list[str] = []
        self.action = self.determine_action()
        self.status = "Open"
        self.resolved_by = None
        self.resolved_at = None
        self.resolution_notes = None

    def calculate_score(self) -> int:
        return self.severity_scores.get(self.severity, 0)

    def apply_threat_intelligence(
        self,
        threat: dict[str, str | int] | None
    ) -> None:

        if threat:
            self.score += threat["risk"]
            self.notes.append(threat["reason"])
            self.action = self.determine_action()

    def determine_action(self) -> str:
        if self.score >= 20:
            return "Escalate"
        elif self.score >= 10:
            return "Investigate"
        else:
            return "Monitor"
        
    def update_status(self, new_status: str) -> None:
        valid_statuses = {
            "Open",
            "Investigating",
            "Resolved"
        }

        if new_status not in valid_statuses:
            raise ValueError("Invalid status.")

        valid_transitions = {
            "Open": {"Investigating"},
            "Investigating": {"Resolved"},
            "Resolved": set()
        }

        if new_status not in valid_transitions[self.status]:
            raise ValueError(
                f"Invalid status transition: "
                f"{self.status} -> {new_status}"
            )

        self.status = new_status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "severity": self.severity,
            "user": self.user,
            "ip": self.ip,
            "score": self.score,
            "notes": self.notes,
            "action": self.action,
            "status": self.status,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at
        }
    
    def resolve(self, resolved_by: str, resolution_notes: str) -> None:

        if self.status != "Investigating":
            raise ValueError(
                "Incident must be Investigating before it can be resolved"
            )

        if not resolved_by:
            raise ValueError("resolved_by is required")

        if not resolution_notes:
            raise ValueError("resolution_notes is required")

        self.status = "Resolved"
        self.resolved_by = resolved_by
        self.resolved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.resolution_notes = resolution_notes

