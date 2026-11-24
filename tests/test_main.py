

import runpy

from incident import Incident
from main import get_incident, list_incidents, main


class FakeRepository:
    def __init__(self, incidents=None):
        self.incidents = incidents or []

    def load(self):
        return [incident.to_dict() for incident in self.incidents]

    def get_by_id(self, incident_id):
        for incident in self.incidents:
            if incident.id == incident_id:
                return incident

        return None

    def save(self, incident):
        self.incidents.append(incident)


class FakeAlertService:
    def __init__(self):
        self.alerted_incidents = []

    def notify(self, incident):
        self.alerted_incidents.append(incident)


def make_incident():
    return Incident(
        "INC-001",
        "2026-08-29 16:00:00",
        "WARNING",
        "admin",
        "192.168.1.50"
    )


def test_list_incidents_empty_repository(capsys):
    repository = FakeRepository()

    list_incidents(repository)

    captured = capsys.readouterr()
    assert "No incidents found." in captured.out


def test_list_incidents_with_records(capsys):
    repository = FakeRepository([make_incident()])

    list_incidents(repository)

    captured = capsys.readouterr()
    assert "Aegis Incidents" in captured.out
    assert "INC-001" in captured.out
    assert "admin" in captured.out


def test_get_incident_not_found(capsys):
    repository = FakeRepository()

    get_incident(repository, "INC-999")

    captured = capsys.readouterr()
    assert "Incident INC-999 not found." in captured.out


def test_get_incident_found(capsys):
    repository = FakeRepository([make_incident()])

    get_incident(repository, "INC-001")

    captured = capsys.readouterr()
    assert "INC-001" in captured.out
    assert "admin" in captured.out
    assert "192.168.1.50" in captured.out


def test_main_processes_log_file(tmp_path, capsys):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    log_file = tmp_path / "security.log"
    log_file.write_text(
        "2026-08-29 16:00:00 WARNING login failed "
        "user admin 192.168.1.50\n"
        "invalid log entry\n"
    )

    result = main(
        repository=repository,
        alert_service=alert_service,
        file_path=str(log_file)
    )

    captured = capsys.readouterr()

    assert len(result.incidents) == 1
    assert result.invalid_logs == 1
    assert "Processed: 1" in captured.out
    assert "Invalid: 1" in captured.out
    assert len(repository.incidents) == 1


def test_cli_get_command(monkeypatch, capsys):
    repository = FakeRepository([make_incident()])

    monkeypatch.setattr(
        "main.JSONIncidentRepository",
        lambda: repository
    )
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "get", "INC-001"]
    )

    runpy.run_module("main", run_name="__main__")

    captured = capsys.readouterr()
    assert "INC-001" in captured.out


def test_cli_list_command(monkeypatch, capsys):
    repository = FakeRepository([make_incident()])

    monkeypatch.setattr(
        "main.JSONIncidentRepository",
        lambda: repository
    )
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "list"]
    )

    runpy.run_module("main", run_name="__main__")

    captured = capsys.readouterr()
    assert "Aegis Incidents" in captured.out

def test_main_creates_default_dependencies(monkeypatch):
    repository = FakeRepository()
    alert_service = FakeAlertService()
    captured = {}

    monkeypatch.setattr(
        "main.JSONIncidentRepository",
        lambda: repository
    )

    monkeypatch.setattr(
        "main.EmailAlert",
        lambda: object()
    )

    def fake_alert_service(alert):
        captured["alert"] = alert
        return alert_service

    monkeypatch.setattr(
        "main.AlertService",
        fake_alert_service
    )

    def fake_aegis(**kwargs):
        captured["aegis_dependencies"] = kwargs
        return type(
            "FakeAegis",
            (),
            {
                "process_log": lambda self, log, incident_id:
                    make_incident()
            }
        )()

    monkeypatch.setattr("main.Aegis", fake_aegis)

    result = main()

    assert result.id == "INC-001"
    assert captured["aegis_dependencies"]["repository"] is repository
    assert captured["aegis_dependencies"]["alert_service"] is alert_service
    assert captured["alert"] is not None



def test_cli_fallback_runs_main(monkeypatch, capsys):
    class FakeAegis:
        def __init__(self, **kwargs):
            pass

        def process_log(self, log, incident_id):
            return make_incident()

    monkeypatch.setattr(
        "repos.JSONIncidentRepository",
        lambda: FakeRepository()
    )

    monkeypatch.setattr(
        "aegis.Aegis",
        FakeAegis
    )

    monkeypatch.setattr(
        "sys.argv",
        ["main.py"]
    )

    runpy.run_module("main", run_name="__main__")

    captured = capsys.readouterr()
    assert "Incident ID: INC-001" in captured.out


def test_cli_unknown_command_runs_main(monkeypatch, capsys):
    class FakeAegis:
        def __init__(self, **kwargs):
            pass

        def process_log(self, log, incident_id):
            return make_incident()

    monkeypatch.setattr(
        "repos.JSONIncidentRepository",
        lambda: FakeRepository()
    )

    monkeypatch.setattr(
        "aegis.Aegis",
        FakeAegis
    )

    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "unknown"]
    )

    runpy.run_module("main", run_name="__main__")

    captured = capsys.readouterr()
    assert "Incident ID: INC-001" in captured.out
