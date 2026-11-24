
import json
from incident import Incident
from repos import JSONIncidentRepository

def test_json_repository_preserves_multiple_incidents(tmp_path, monkeypatch):
    incident_1 = Incident(
        "INC-001",
        "2026-08-29 16:30:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )

    incident_2 = Incident(
        "INC-002",
        "2026-08-29 16:35:00",
        "WARNING",
        "jsmith",
        "192.168.1.50"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident_1)
    repository.save(incident_2)

    file_path = tmp_path / "incidents.json"

    with open(file_path, "r") as file:
        data = json.load(file)

    assert len(data) == 2
    assert data[0]["id"] == "INC-001"
    assert data[1]["id"] == "INC-002"
    assert data[0]["status"] == "Open"
    assert data[1]["status"] == "Open"
    
def test_json_repository_saves_updated_status(tmp_path, monkeypatch):
    incident = Incident(
        "INC-003",
        "2026-08-29 17:00:00",
        "WARNING",
        "alice",
        "192.168.1.30"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    incident.update_status("Investigating")
    repository.save(incident)

    file_path = tmp_path / "incidents.json"

    with open(file_path, "r") as file:
        data = json.load(file)

    assert data[0]["id"] == "INC-003"
    assert data[0]["status"] == "Investigating"
    
def test_json_repository_loads_incidents(tmp_path, monkeypatch):
    incident = Incident(
        "INC-004",
        "2026-08-29 18:00:00",
        "CRITICAL",
        "admin",
        "192.168.1.40"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident)

    incidents = repository.load()

    assert len(incidents) == 1
    assert incidents[0]["id"] == "INC-004"
    assert incidents[0]["severity"] == "CRITICAL"
    assert incidents[0]["status"] == "Open"
    
def test_json_repository_gets_incident_by_id(tmp_path, monkeypatch):
    incident = Incident(
        "INC-005",
        "2026-08-29 18:30:00",
        "WARNING",
        "jsmith",
        "192.168.1.50"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident)

    result = repository.get_by_id("INC-005")

    assert result is not None
    assert result.id == "INC-005"
    assert result.user == "jsmith"
    assert result.status == "Open"
    
def test_json_repository_updates_incident(tmp_path, monkeypatch):
    incident = Incident(
        "INC-006",
        "2026-08-29 19:00:00",
        "WARNING",
        "admin",
        "192.168.1.60"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident)

    repository.update(
        "INC-006",
        {"status": "Investigating"}
    )

    result = repository.get_by_id("INC-006")

    assert result is not None
    assert result.status == "Investigating"
    
def test_json_repository_persists_status_transition(
    tmp_path,
    monkeypatch
):
    incident = Incident(
        "INC-007",
        "2026-08-29 19:30:00",
        "WARNING",
        "admin",
        "192.168.1.70"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident)

    incident.update_status("Investigating")

    repository.update(
        incident.id,
        {"status": incident.status}
    )

    loaded = repository.get_by_id("INC-007")

    assert loaded is not None
    assert loaded.status == "Investigating"
    
def test_json_repository_returns_none_for_missing_incident(
    tmp_path,
    monkeypatch
):
    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    result = repository.get_by_id("INC-999")

    assert result is None
    
def test_json_repository_persists_updated_status(tmp_path, monkeypatch):
    incident = Incident(
        "INC-007",
        "2026-08-29 19:30:00",
        "WARNING",
        "admin",
        "192.168.1.70"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    # Save the incident
    repository.save(incident)

    # Update its status
    repository.update(
        "INC-007",
        {"status": "Investigating"}
    )

    # Create a new repository instance.
    # This simulates Aegis restarting.
    new_repository = JSONIncidentRepository()

    result = new_repository.get_by_id("INC-007")

    assert result.id == "INC-007"
    assert result.status == "Investigating"
    
def test_json_repository_handles_missing_file(tmp_path, monkeypatch):
        repository = JSONIncidentRepository()

        monkeypatch.chdir(tmp_path)

        repository.save(
            Incident(
                "INC-009",
                "2026-08-29 20:00:00",
                "INFO",
                "admin",
                "192.168.1.90"
            )
        )

        incidents = repository.load()

        assert len(incidents) == 1
        assert incidents[0]["id"] == "INC-009"

def test_json_repository_load_returns_empty_when_file_missing(tmp_path, monkeypatch):
    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    incidents = repository.load()

    assert incidents == []

def test_json_repository_get_by_id_returns_incident(tmp_path, monkeypatch):
    incident = Incident(
        "INC-024",
        "2026-08-30 00:00:00",
        "WARNING",
        "admin",
        "192.168.1.100"
    )

    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    repository.save(incident)

    result = repository.get_by_id("INC-024")

    assert isinstance(result, Incident)
    assert result.id == "INC-024"
    assert result.severity == "WARNING"
    assert result.user == "admin"
    assert result.ip == "192.168.1.100"
    
def test_json_repository_converts_single_dict_to_list(tmp_path, monkeypatch):
    repository = JSONIncidentRepository()

    monkeypatch.chdir(tmp_path)

    with open("incidents.json", "w") as file:
        json.dump(
            {
                "id": "INC-028",
                "time": "2026-08-30 01:00:00",
                "severity": "WARNING",
                "user": "admin",
                "ip": "192.168.1.110",
                "score": 5,
                "notes": "",
                "action": "Monitor",
                "status": "Open",
                "resolved_by": None,
                "resolution_notes": None,
                "resolved_at": None
            },
            file
        )

    incidents = repository.load()

    assert isinstance(incidents, list)
    assert len(incidents) == 1
    assert incidents[0]["id"] == "INC-028"