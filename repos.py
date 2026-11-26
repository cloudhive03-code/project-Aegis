

import json
import os
import tempfile
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

    def _write_incidents(self, incidents: list[dict]) -> None:
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=".",
                prefix=".incidents.",
                suffix=".tmp",
                delete=False
            ) as file:
                temp_path = file.name

                json.dump(incidents, file, indent=4)

                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, "incidents.json")
            temp_path = None

        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass

    def save(self, incident: Incident) -> None:
        incidents = self.load()
        incidents.append(incident.to_dict())

        self._write_incidents(incidents)

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

        self._write_incidents(incidents)
