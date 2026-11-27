
import json
import repos
from incident import Incident
import multiprocessing
import os
import portalocker
from concurrent.futures import ProcessPoolExecutor
import pytest
from exceptions import RepositoryDataError
from repos import JSONIncidentRepository
from concurrent.futures import ThreadPoolExecutor

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


def test_json_repository_raises_error_for_corrupted_file(
    tmp_path,
    monkeypatch
):
    repository = JSONIncidentRepository()
    monkeypatch.chdir(tmp_path)

    with open("incidents.json", "w") as file:
        file.write('{"id": "INC-001", invalid json}')

    with pytest.raises(RepositoryDataError):
        repository.load()


def test_json_repository_does_not_overwrite_corrupted_file(
    tmp_path,
    monkeypatch
):
    repository = JSONIncidentRepository()
    monkeypatch.chdir(tmp_path)

    corrupted_content = '{"id": "INC-001", invalid json}'

    with open("incidents.json", "w") as file:
        file.write(corrupted_content)

    incident = Incident(
        "INC-002",
        "2026-08-29 20:00:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    with pytest.raises(RepositoryDataError):
        repository.save(incident)

    with open("incidents.json", "r") as file:
        saved_content = file.read()

    assert saved_content == corrupted_content

@pytest.mark.parametrize("operation", ["save", "update"])
def test_repository_preserves_original_file_when_replace_fails(
    tmp_path,
    monkeypatch,
    operation
):
    repository = JSONIncidentRepository()
    monkeypatch.chdir(tmp_path)

    original_incident = Incident(
        "INC-030",
        "2026-08-30 02:00:00",
        "WARNING",
        "admin",
        "192.168.1.120"
    )

    repository.save(original_incident)

    original_content = (tmp_path / "incidents.json").read_text(
        encoding="utf-8"
    )

    def fail_replace(source, destination):
        raise OSError("Simulated replacement failure")

    monkeypatch.setattr(repos.os, "replace", fail_replace)

    with pytest.raises(OSError, match="Simulated replacement failure"):
        if operation == "save":
            repository.save(
                Incident(
                    "INC-031",
                    "2026-08-30 02:05:00",
                    "CRITICAL",
                    "root",
                    "192.168.1.130"
                )
            )
        else:
            repository.update(
                "INC-030",
                {"status": "Investigating"}
            )

    saved_content = (tmp_path / "incidents.json").read_text(
        encoding="utf-8"
    )

    assert saved_content == original_content

    temporary_files = list(tmp_path.glob(".incidents.*.tmp"))
    assert temporary_files == []

def _save_incident_in_process(directory, number):
    os.chdir(directory)

    repository = JSONIncidentRepository()

    incident = Incident(
        f"INC-{number:03}",
        "2026-08-30 04:00:00",
        "WARNING",
        "admin",
        "192.168.1.160"
    )

    repository.save(incident)

    return incident.id

def test_repository_preserves_incidents_from_concurrent_threads(
    tmp_path,
    monkeypatch
):
    monkeypatch.chdir(tmp_path)

    incident_count = 40

    def save_incident(number):
        repository = JSONIncidentRepository()

        incident = Incident(
            f"INC-{number:03}",
            "2026-08-30 03:00:00",
            "WARNING",
            "admin",
            "192.168.1.150"
        )

        repository.save(incident)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(save_incident, range(incident_count)))

    repository = JSONIncidentRepository()
    saved_incidents = repository.load()

    assert len(saved_incidents) == incident_count

    saved_ids = {incident["id"] for incident in saved_incidents}

    assert len(saved_ids) == incident_count

def test_repository_preserves_incidents_from_concurrent_processes(
    tmp_path
):
    incident_count = 40

    context = multiprocessing.get_context("spawn")

    with ProcessPoolExecutor(
        max_workers=4,
        mp_context=context
    ) as executor:
        saved_ids = list(
            executor.map(
                _save_incident_in_process,
                [str(tmp_path)] * incident_count,
                range(incident_count)
            )
        )

    repository = JSONIncidentRepository()

    # Read the file from the test directory.
    original_directory = os.getcwd()

    try:
        os.chdir(tmp_path)
        saved_incidents = repository.load()
    finally:
        os.chdir(original_directory)

    assert len(saved_incidents) == incident_count
    assert len(saved_ids) == incident_count
    assert len(set(saved_ids)) == incident_count

    stored_ids = {
        incident["id"] for incident in saved_incidents
    }

    assert stored_ids == set(saved_ids)


def test_repository_handles_missing_temp_file_during_cleanup(
    tmp_path,
    monkeypatch
):
    repository = JSONIncidentRepository()
    monkeypatch.chdir(tmp_path)

    original_incident = Incident(
        "INC-040",
        "2026-08-30 05:00:00",
        "WARNING",
        "admin",
        "192.168.1.170"
    )

    repository.save(original_incident)

    original_content = (tmp_path / "incidents.json").read_text(
        encoding="utf-8"
    )

    def remove_temp_then_fail(source, destination):
        os.unlink(source)
        raise OSError("Simulated replacement failure")

    monkeypatch.setattr(
        repos.os,
        "replace",
        remove_temp_then_fail
    )

    with pytest.raises(OSError, match="Simulated replacement failure"):
        repository.save(
            Incident(
                "INC-041",
                "2026-08-30 05:05:00",
                "CRITICAL",
                "root",
                "192.168.1.180"
            )
        )

    saved_content = (tmp_path / "incidents.json").read_text(
        encoding="utf-8"
    )

    assert saved_content == original_content

    temporary_files = list(tmp_path.glob(".incidents.*.tmp"))
    assert temporary_files == []

def _hold_repository_file_lock(directory, lock_acquired, release_lock):
    os.chdir(directory)

    with portalocker.Lock("incidents.json.lock", mode="a"):
        lock_acquired.set()
        release_lock.wait(timeout=10)

def test_repository_raises_when_lock_timeout_expires(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    context = multiprocessing.get_context("spawn")
    lock_acquired = context.Event()
    release_lock = context.Event()

    process = context.Process(
        target=_hold_repository_file_lock,
        args=(str(tmp_path), lock_acquired, release_lock)
    )

    process.start()

    try:
        assert lock_acquired.wait(timeout=5)

        repository = JSONIncidentRepository()

        incident = Incident(
            "INC-050",
            "2026-08-30 06:00:00",
            "WARNING",
            "admin",
            "192.168.1.190"
        )

        with pytest.raises(portalocker.AlreadyLocked):
            repository.save(incident)

    finally:
        release_lock.set()
        process.join(timeout=5)

        if process.is_alive():
            process.terminate()
            process.join()

    assert process.exitcode == 0


def test_repository_releases_lock_after_write_failure(
    tmp_path,
    monkeypatch
):
    monkeypatch.chdir(tmp_path)

    repository = JSONIncidentRepository()

    incident = Incident(
        "INC-051",
        "2026-08-30 06:10:00",
        "WARNING",
        "admin",
        "192.168.1.191"
    )

    original_write = repository._write_incidents

    def simulate_write_failure(incidents):
        raise OSError("Simulated write failure")

    monkeypatch.setattr(
        repository,
        "_write_incidents",
        simulate_write_failure
    )

    with pytest.raises(OSError, match="Simulated write failure"):
        repository.save(incident)

    # Restore the original write method without resetting the directory.
    monkeypatch.setattr(
        repository,
        "_write_incidents",
        original_write
    )

    # Verify that the repository can acquire the lock again.
    repository.save(incident)

    saved_incidents = repository.load()

    assert len(saved_incidents) == 1
    assert saved_incidents[0]["id"] == "INC-051"

def test_repository_rejects_corrupted_json_without_modifying_file(
    tmp_path,
    monkeypatch
):
    monkeypatch.chdir(tmp_path)

    repository = JSONIncidentRepository()

    corrupted_content = '{"id": "INC-001", "severity": '

    (tmp_path / "incidents.json").write_text(
        corrupted_content,
        encoding="utf-8"
    )

    with pytest.raises(RepositoryDataError):
        repository.load()

    saved_content = (tmp_path / "incidents.json").read_text(
        encoding="utf-8"
    )

    assert saved_content == corrupted_content