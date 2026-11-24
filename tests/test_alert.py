
from alert import AlertService, EmailAlert, IncidentIdGapNotifier, SMSAlert
from incident import Incident
from models import IncidentIdGap


class FakeAlert:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)
def test_email_alert(capsys):
    alert = EmailAlert()

    alert.send("Test email alert")

    captured = capsys.readouterr()

    assert captured.out == "Email: Test email alert\n"


def test_sms_alert(capsys):
    alert = SMSAlert()

    alert.send("Test SMS alert")

    captured = capsys.readouterr()

    assert captured.out == "SMS: Test SMS alert\n"


def test_alert_service(capsys):
    incident = Incident(
        "INC-001",
        "2026-08-29 16:00:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )

    alert = EmailAlert()
    service = AlertService(alert)

    service.notify(incident)

    captured = capsys.readouterr()

    expected_message = (
        "Email: CRITICAL incident detected! "
        "ID: INC-001, "
        "User: admin, "
        "IP: 192.168.1.20, "
        "Score: 10, "
        "Action: Investigate\n"
    )

    assert captured.out == expected_message
    
def test_incident_id_gap_notifier_sends_alert():
    alert = FakeAlert()

    notifier = IncidentIdGapNotifier(alert)

    gap = IncidentIdGap(
        missing_ids=["INC-002", "INC-004"]
    )

    notifier.notify(gap)

    assert len(alert.messages) == 1
    assert "INC-002" in alert.messages[0]
    assert "INC-004" in alert.messages[0]
    assert "unclassified incident ID sequence anomaly" in alert.messages[0]