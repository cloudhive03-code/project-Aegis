  
    
from main import main
from pytest import CaptureFixture

from aegis import Aegis


class FakeRepository:
    def __init__(self):
        self.saved_incidents = []

    def save(self, incident):
        self.saved_incidents.append(incident)
        
    def get_by_id(self, incident_id):
        for incident in self.saved_incidents:
            if incident.id == incident_id:
                return incident
        return None


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


def test_aegis_does_not_alert_non_escalated_incident():
    repository = FakeRepository()
    alert_service = FakeAlertService()

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    incident = aegis.process_log(
        "2026-08-29 16:05:00 INFO login successful user admin 192.168.1.20",
        "INC-002"
    )

    assert incident.id == "INC-002"
    assert incident.severity == "INFO"
    assert incident.score == 1
    assert incident.action == "Monitor"

    assert repository.saved_incidents[0] is incident
    assert alert_service.alerted_incidents == []
    
def test_main_processes_incident(capsys: CaptureFixture[str]):
    repository = FakeRepository()
    alert_service = FakeAlertService()

    incident = main(
        repository=repository,
        alert_service=alert_service
    )

    captured = capsys.readouterr()

    assert incident.id == "INC-001"
    assert incident.user == "jsmith"
    assert incident.ip == "192.168.1.50"

    assert repository.saved_incidents[0] is incident
    assert alert_service.alerted_incidents[0] is incident

    assert "Incident ID: INC-001" in captured.out
    assert "User: jsmith" in captured.out
    assert "IP: 192.168.1.50" in captured.out