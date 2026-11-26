
import json
from typing import Protocol

from incident import Incident


class IncidentRepository(Protocol):
    def save(self, incident: Incident) -> None:
        ...
    
    def load(self) -> list[dict]:
        ...
        
    def get_by_id(self, incident_id: str) -> Incident | None:
        ...
        
    def update(self, incident_id: str, updates: dict) -> None:
        ...


class JSONIncidentRepository:
    def save(self, incident: Incident) -> None:
        incidents = self.load()
        incidents.append(incident.to_dict())

        with open("incidents.json", "w") as file:
            json.dump(incidents, file, indent=4)

    def load(self) -> list[dict]:
        try:
            with open("incidents.json", "r") as file:
                incidents = json.load(file)
        except FileNotFoundError:
            return []

        if isinstance(incidents, dict):
            incidents = [incidents]

        return incidents

    
    def get_by_id(self, incident_id: str) -> Incident | None:
        incidents = self.load()

        for data in incidents:
            if data["id"] == incident_id:
                incident = Incident(
                    data["id"],
                    data["time"],
                    data["severity"],
                    data["user"],
                    data["ip"]
                )

                incident.score = data["score"]
                incident.notes = data["notes"]
                incident.action = data["action"]
                incident.status = data.get("status", "Open")
                incident.resolved_by = data.get("resolved_by")
                incident.resolution_notes = data.get("resolution_notes")
                incident.resolved_at = data.get("resolved_at")

                return incident

        return None
    
    def update(self, incident_id: str, updates: dict) -> None:
        incidents = self.load()

        for incident in incidents:
            if incident["id"] == incident_id:
                incident.update(updates)
                break

        with open("incidents.json", "w") as file:
            json.dump(
                incidents,
                file,
                indent=4
            )
            
    