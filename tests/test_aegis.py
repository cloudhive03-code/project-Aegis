
import pytest

from exceptions import LogParseError, NotificationError
from incident import Incident
from repos import JSONIncidentRepository
from service import AegisService

from aegis import Aegis

class FakeRepository:
    def __init__(self):
        self.saved_incidents = []

    def save(self, incident):
        self.saved_incidents.append(incident)
        
    def load(self):
        return [incident.to_dict() for incident in self.saved_incidents]

    def get_by_id(self, incident_id):
        for incident in self.saved_incidents:
            if incident.id == incident_id:
                return incident

        return None

    def update(self, incident_id, updates):
        incident = self.get_by_id(incident_id)

        if incident is None:
            return

        for key, value in updates.items():
            setattr(incident, key, value)


class FakeAlertService:
    def __init__(self):
        self.alerted_incidents = []

    def notify(self, incident):
        self.alerted_incidents.append(incident)

class FakeAuditLogger:
    def __init__(self):
        self.messages = []

    def record(self, message):
        self.messages.append(message)
        
class FakeGapNotifier:
    def __init__(self):
        self.gaps = []
    def notify(self, gap):
        self.gaps.append(gap)
        
class FailingGapNotifier:
    def notify(self, gap):
        raise NotificationError("Notification service unavailable")

def test_aegis_processes_log():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = aegis.process_log(
        "2026-08-29 16:00:00 CRITICAL login failed user admin 192.168.10.45",
        "INC-001"
    )

    assert incident.id == "INC-001"
    assert incident.severity == "CRITICAL"
    assert incident.user == "admin"
    assert incident.ip == "192.168.10.45"

    assert incident.score == 25
    assert incident.action == "Escalate"

    assert repository.saved_incidents[0] is incident
    assert alert_service.alerted_incidents[0] is incident
    
def test_aegis_updates_incident_status():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = Incident(
        "INC-008",
        "2026-08-29 20:00:00",
        "WARNING",
        "admin",
        "192.168.1.80"
    )

    repository.save(incident)

    aegis.update_incident_status(
        "INC-008",
        "Investigating"
    )

    assert incident.status == "Investigating"
    
def test_aegis_rejects_missing_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    with pytest.raises(ValueError, match="Incident INC-999 not found."):
        aegis.update_incident_status(
            "INC-999",
            "Investigating"
        )
        
def test_aegis_does_not_alert_for_non_escalated_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = aegis.process_log(
        "2026-08-29 21:45:00 INFO login successful user alice 192.168.1.80",
        "INC-017"
    )

    assert incident.action == "Monitor"
    assert alert_service.alerted_incidents == []
    
def test_aegis_does_not_alert_for_investigating_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = aegis.process_log(
        "2026-08-29 22:00:00 CRITICAL login failed user alice 192.168.1.80",
        "INC-018"
    )

    assert incident.action == "Investigate"
    assert alert_service.alerted_incidents == []
    
def test_aegis_persists_incident_status_update():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = Incident(
        "INC-019",
        "2026-08-29 22:30:00",
        "WARNING",
        "admin",
        "192.168.1.90"
    )

    repository.save(incident)

    aegis.update_incident_status(
        "INC-019",
        "Investigating"
    )

    result = repository.get_by_id("INC-019")

    assert result.status == "Investigating"
    
def test_aegis_resolves_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = Incident(
        "INC-023",
        "2026-08-29 23:00:00",
        "WARNING",
        "admin",
        "192.168.1.90"
    )

    incident.update_status("Investigating")
    repository.save(incident)

    aegis.resolve_incident(
        "INC-023",
        "analyst1",
        "Failed login activity investigated and contained"
    )

    result = repository.get_by_id("INC-023")

    assert result.status == "Resolved"
    assert result.resolved_by == "analyst1"
    assert result.resolution_notes == (
        "Failed login activity investigated and contained"
    )
    assert result.resolved_at is not None

def test_aegis_rejects_resolving_missing_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    with pytest.raises(ValueError, match="Incident INC-999 not found"):
        aegis.resolve_incident(
            "INC-999",
            "analyst1",
            "Incident does not exist"
        )
def test_aegis_does_not_persist_failed_resolution(
    tmp_path,
    monkeypatch
):
    monkeypatch.chdir(tmp_path)

    repository = JSONIncidentRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = Incident(
        "INC-030",
        "2026-11-28 10:00:00",
        "WARNING",
        "admin",
        "192.168.1.90"
    )

    repository.save(incident)

    with pytest.raises(ValueError):
        aegis.resolve_incident(
            "INC-030",
            "analyst1",
            "Investigation completed"
        )

    result = repository.get_by_id("INC-030")

    assert result is not None
    assert result.status == "Open"
    assert result.resolved_by is None
    assert result.resolution_notes is None
    assert result.resolved_at is None
        
def test_aegis_rejects_duplicate_incident_id():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    aegis.process_log(
        "2026-08-29 16:00:00 CRITICAL login failed user admin 192.168.10.45",
        "INC-001"
    )

    with pytest.raises(ValueError, match="Incident INC-001 already exists"):
        aegis.process_log(
            "2026-08-29 16:05:00 WARNING login failed user admin 192.168.1.50",
            "INC-001"
        )

    assert len(repository.saved_incidents) == 1
    
def test_aegis_processes_multiple_logs():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    logs = [
        "2026-08-29 16:00:00 CRITICAL login failed user admin 192.168.10.45",
        "2026-08-29 16:05:00 INFO login successful user alice 192.168.1.20",
    ]

    incidents = aegis.process_logs(logs)

    assert len(incidents) == 2
    assert incidents[0].id == "INC-001"
    assert incidents[1].id == "INC-002"

    assert len(repository.saved_incidents) == 2
    
def test_aegis_generates_next_incident_id():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    first = aegis.process_log(
        "2026-08-30 10:00:00 INFO login successful user alice 192.168.1.20",
        "INC-001"
    )

    second_id = aegis._next_incident_id()

    assert first.id == "INC-001"
    assert second_id == "INC-002"
    
def test_aegis_process_logs_uses_next_available_ids():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    aegis.process_log(
        "2026-08-30 10:00:00 INFO login successful user alice 192.168.1.20",
        "INC-001"
    )

    logs = [
        "2026-08-30 10:05:00 WARNING login failed user bob 192.168.1.30",
        "2026-08-30 10:10:00 INFO login successful user carol 192.168.1.40",
    ]

    incidents = aegis.process_logs(logs)

    assert incidents[0].id == "INC-002"
    assert incidents[1].id == "INC-003"
    assert len(repository.saved_incidents) == 3
    
def test_aegis_processes_log_file(tmp_path):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    log_file = tmp_path / "security.log"

    log_file.write_text(
        "2026-08-30 11:00:00 INFO login successful user alice 192.168.1.20\n"
        "2026-08-30 11:05:00 WARNING login failed user bob 192.168.1.30\n"
    )

    incidents = aegis.process_log_file(str(log_file))

    assert len(incidents) == 2
    assert incidents[0].id == "INC-001"
    assert incidents[1].id == "INC-002"
    assert incidents[0].user == "alice"
    assert incidents[1].user == "bob"
    
def test_aegis_rejects_missing_log_file(tmp_path):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    missing_file = tmp_path / "missing.log"

    with pytest.raises(FileNotFoundError):
        aegis.process_log_file(str(missing_file))
        
def test_aegis_rejects_invalid_log_file(tmp_path):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    log_file = tmp_path / "security.log"

    log_file.write_text(
        "this is not a valid log\n"
    )

    with pytest.raises(LogParseError):
        aegis.process_log_file(str(log_file))
        
def test_aegis_safe_log_file_skips_invalid_logs(tmp_path):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    log_file = tmp_path / "security.log"

    log_file.write_text(
    "2026-08-30 12:00:00 INFO login successful user alice 192.168.1.20\n"
    "\n"
    "invalid log entry\n"
    "   \n"
    "2026-08-30 12:05:00 WARNING login failed user bob 192.168.1.30\n"
)

    result = aegis.process_log_file_safe(str(log_file))
    incidents = result.incidents

    assert len(incidents) == 2
    assert result.invalid_logs == 1
    assert incidents[0].id == "INC-001"
    assert incidents[1].id == "INC-002"
    assert incidents[0].user == "alice"
    assert incidents[1].user == "bob"
    
def test_service_detects_incident_id_gaps():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service
    )

    result = service.check_incident_id_sequence()

    assert result.next_id == "INC-004"
    assert result.missing_ids == ["INC-002"]
    
def test_service_reports_incident_id_gap(capsys):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service
    )

    service.next_incident_id()

    captured = capsys.readouterr()

    assert "Incident ID sequence gap detected" in captured.out
    assert "INC-002" in captured.out
    
def test_service_creates_gap_event():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service
    )

    gap = service.detect_incident_id_gap()

    assert gap is not None
    assert gap.missing_ids == ["INC-002"]
    
def test_service_returns_no_gap_when_sequence_is_complete():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-002",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service
    )

    gap = service.detect_incident_id_gap()

    assert gap is None
    
def test_service_audits_incident_id_gap():
    repository = FakeRepository()
    alert_service = FakeAlertService()
    audit_logger = FakeAuditLogger()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service,
        audit_logger=audit_logger
    )

    gap = service.detect_incident_id_gap()

    assert gap is not None
    assert gap.missing_ids == ["INC-002"]
    assert len(audit_logger.messages) == 1
    assert "INC-002" in audit_logger.messages[0]
    
def test_service_notifies_incident_id_gap():
    repository = FakeRepository()
    alert_service = FakeAlertService()
    audit_logger = FakeAuditLogger()
    gap_notifier = FakeGapNotifier()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service,
        audit_logger=audit_logger,
        gap_notifier=gap_notifier
    )

    gap = service.detect_incident_id_gap()

    assert gap is not None
    assert len(gap_notifier.gaps) == 1
    assert gap_notifier.gaps[0].missing_ids == ["INC-002"]
    
def test_service_audits_gap_notification_failure():
    repository = FakeRepository()
    alert_service = FakeAlertService()
    audit_logger = FakeAuditLogger()
    gap_notifier = FailingGapNotifier()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    repository.save(
        Incident(
            "INC-003",
            "2026-08-30 12:05:00",
            "INFO",
            "bob",
            "192.168.1.30"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service,
        audit_logger=audit_logger,
        gap_notifier=gap_notifier
    )

    gap = service.detect_incident_id_gap()

    assert gap is not None
    assert gap.missing_ids == ["INC-002"]

    assert len(audit_logger.messages) == 2

    assert "INC-002" in audit_logger.messages[0]
    assert "Gap notification failed" in audit_logger.messages[1]
    assert "Notification service unavailable" in audit_logger.messages[1]


def test_service_generates_next_incident_id():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    repository.save(
        Incident(
            "INC-001",
            "2026-08-30 12:00:00",
            "INFO",
            "alice",
            "192.168.1.20"
        )
    )

    service = AegisService(
        repository=repository,
        alert_service=alert_service
    )

    result = service.generate_incident_id()

    assert result.next_id == "INC-002"
    assert result.missing_ids == []
