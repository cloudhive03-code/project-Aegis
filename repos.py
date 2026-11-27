import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Iterator, Protocol

import portalocker

from exceptions import RepositoryDataError
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


_REPOSITORY_THREAD_LOCK = RLock()

VALID_STATUSES = {
    "Open",
    "Investigating",
    "Resolved"
}

ALLOWED_UPDATE_FIELDS = {
    "status",
    "resolved_by",
    "resolution_notes",
    "resolved_at"
}


@contextmanager
def _repository_lock() -> Iterator[None]:
    lock_path = Path("incidents.json.lock").resolve()

    with _REPOSITORY_THREAD_LOCK:
        with portalocker.Lock(
            lock_path,
            mode="a",
            timeout=5,
            check_interval=0.05,
            fail_when_locked=False
        ):
            yield


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
        with _repository_lock():
            incidents = self.load()
            incidents.append(incident.to_dict())

            self._write_incidents(incidents)

    def load(self) -> list[dict]:
        try:
            with open("incidents.json", "r", encoding="utf-8") as file:
                incidents = json.load(file)

        except FileNotFoundError:
            return []

        except json.JSONDecodeError as error:
            raise RepositoryDataError(
                "The incident database contains invalid JSON."
            ) from error

        if isinstance(incidents, dict):
            incidents = [incidents]

        return self._validate_incidents(incidents)

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

        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary.")

        if not updates:
            raise ValueError("Updates cannot be empty.")

        forbidden_fields = set(updates) - ALLOWED_UPDATE_FIELDS

        if forbidden_fields:
            raise ValueError(
                f"Updates contain forbidden fields: "
                f"{sorted(forbidden_fields)}"
            )

        with _repository_lock():
            incidents = self.load()

            for incident in incidents:
                if incident["id"] == incident_id:

                    incident.update(updates)

                    self._validate_incidents(incidents)

                    self._write_incidents(incidents)
                    return

            raise ValueError(
                f"Incident {incident_id} not found."
            )

    def _validate_incidents(self, incidents: object) -> list[dict]:

        # Support a legacy database containing a single incident.
        if isinstance(incidents, dict):
            incidents = [incidents]

        if not isinstance(incidents, list):
            raise RepositoryDataError(
                "The incident database must contain a list of incidents."
            )

        required_fields = {
            "id": str,
            "time": str,
            "severity": str,
            "user": str,
            "ip": str,
            "score": int,
            "notes": list,
            "action": str
        }

        optional_fields = {
            "status": str,
            "resolved_by": (str, type(None)),
            "resolution_notes": (str, type(None)),
            "resolved_at": (str, type(None))
        }

        for index, incident in enumerate(incidents):

            # Every incident must be a dictionary.
            if not isinstance(incident, dict):
                raise RepositoryDataError(
                    f"Incident at index {index} must be a dictionary."
                )

            # Normalize legacy empty-string notes BEFORE type validation.
            if incident.get("notes") == "":
                incident["notes"] = []

            # Validate required fields.
            for field, expected_type in required_fields.items():

                if field not in incident:
                    raise RepositoryDataError(
                        f"Incident at index {index} is missing '{field}'."
                    )

                value = incident[field]

                # Reject bool because bool is a subclass of int.
                if field == "score":
                    valid_type = (
                        isinstance(value, int)
                        and not isinstance(value, bool)
                    )
                else:
                    valid_type = isinstance(value, expected_type)

                if not valid_type:
                    raise RepositoryDataError(
                        f"Incident at index {index} has an invalid '{field}' value."
                    )

            # Validate that every note is a string.
            if not all(
                isinstance(note, str) for note in incident["notes"]
            ):
                raise RepositoryDataError(
                    f"Incident at index {index} contains invalid notes."
                )

            # Validate optional fields.
            for field, expected_type in optional_fields.items():

                if field in incident and not isinstance(
                    incident[field], expected_type
                ):
                    raise RepositoryDataError(
                        f"Incident at index {index} has an invalid '{field}' value."
                    )

            # Validate allowed incident statuses.
            if incident.get("status", "Open") not in VALID_STATUSES:
                raise RepositoryDataError(
                    f"Incident at index {index} has an invalid status."
                )

        return incidents
