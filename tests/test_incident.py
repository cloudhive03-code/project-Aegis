
import pytest
from incident import Incident


def test_incident_creation():
    incident = Incident(
        "INC-001",
        "2026-08-15 16:40:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )
    assert incident.id == "INC-001"
    assert incident.severity == "CRITICAL"
    assert incident.user == "admin"
    assert incident.ip == "192.168.1.20"
    
def test_critical_incident_score():
    incident = Incident(
        "INC-002",
        "2026-08-15 16:40:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )
    incident.score = 20
    assert incident.score == 20
    
def test_escalated_decision():
    incident = Incident(
        "INC-003",
        "2026-08-15 16:40:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )
    incident.score = 20
    assert incident.determine_action() == "Escalate"
    
def test_investigate_decision():
    incident = Incident(
        "INC-004",
        "2026-08-15 16:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )
    incident.score = 10
    assert incident.determine_action() == "Investigate"
    
def test_monitor_decision():
    incident = Incident(
        "INC-005",
        "2026-08-15 16:40:00",
        "INFO",
        "admin",
        "192.168.1.20"
    )
    incident.score = 5
    assert incident.determine_action() == "Monitor"

def test_critical_severity_score():
    incident = Incident(
        "INC-006",
        "2026-08-15 16:40:00",
        "CRITICAL",
        "admin",
        "192.168.1.20"
    )
    assert incident.score == 10
    
def test_warning_severity_score():
    incident = Incident(
        "INC-007",
        "2026-08-15 16:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )
    assert incident.score == 5
    
def test_info_severity_score():
    incident = Incident(
        "INC-008",
        "2026-08-15 16:40:00",
        "INFO",
        "admin",
        "192.168.1.20"
    )
    assert incident.score == 1
    
def test_apply_threat_intelligence_with_no_threat():
    incident = Incident(
        "INC-001",
        "2026-08-29 15:30:00",
        "INFO",
        "alice",
        "192.168.1.10"
    )

    original_score = incident.score
    original_notes = incident.notes.copy()
    original_action = incident.action

    incident.apply_threat_intelligence(None)

    assert incident.score == original_score
    assert incident.notes == original_notes
    assert incident.action == original_action


def test_incident_starts_open():
    incident = Incident(
        "INC-009",
        "2026-08-29 16:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    assert incident.status == "Open"

def test_incident_can_update_status():
    incident = Incident(
        "INC-010",
        "2026-08-29 16:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    incident.update_status("Investigating")

    assert incident.status == "Investigating"

def test_incident_rejects_invalid_status():
    incident = Incident(
        "INC-011",
        "2026-08-29 16:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    with pytest.raises(ValueError):
        incident.update_status("Banana")
        
def test_valid_status_transition():
    incident = Incident(
        "INC-012",
        "2026-08-29 17:00:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    incident.update_status("Investigating")

    assert incident.status == "Investigating"
    
def test_invalid_status_transition():
    incident = Incident(
        "INC-013",
        "2026-08-29 17:00:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    with pytest.raises(ValueError):
        incident.update_status("Closed")
        
def test_incident_can_be_resolved():
    incident = Incident(
        "INC-014",
        "2026-08-29 21:00:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    incident.update_status("Investigating")
    incident.update_status("Resolved")

    assert incident.status == "Resolved"
    
def test_resolved_incident_cannot_return_to_investigating():
    incident = Incident(
        "INC-015",
        "2026-08-29 21:15:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    incident.update_status("Investigating")
    incident.update_status("Resolved")

    with pytest.raises(ValueError):
        incident.update_status("Investigating")
        
def test_open_incident_cannot_skip_investigating():
    incident = Incident(
        "INC-016",
        "2026-08-29 21:30:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    with pytest.raises(ValueError):
        incident.update_status("Resolved")
        
def test_incident_resolution_starts_empty():
    incident = Incident(
        "INC-019",
        "2026-08-29 22:30:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    assert incident.resolved_by is None
    assert incident.resolved_at is None
    assert incident.resolution_notes is None


def test_incident_cannot_resolve_directly_from_open():
    incident = Incident(
        "INC-021",
        "2026-08-29 22:40:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    with pytest.raises(ValueError):
        incident.resolve(
            "analyst1",
            "Investigation completed"
        )
        
def test_incident_rejects_empty_resolution_notes():
    incident = Incident(
        "INC-022",
        "2026-08-29 22:45:00",
        "WARNING",
        "admin",
        "192.168.1.20"
    )

    incident.update_status("Investigating")

    with pytest.raises(ValueError):
        incident.resolve(
            "analyst1",
            ""
        )
        
def test_incident_rejects_empty_resolved_by():
    incident = Incident(
        "INC-025",
        "2026-08-30 00:30:00",
        "WARNING",
        "admin",
        "192.168.1.101"
    )

    incident.update_status("Investigating")

    with pytest.raises(ValueError):
        incident.resolve(
            "",
            "Failed login activity investigated and contained"
        )


def test_incident_cannot_resolve_from_open():
    incident = Incident(
        "INC-027",
        "2026-08-30 00:50:00",
        "WARNING",
        "admin",
        "192.168.1.103"
    )

    with pytest.raises(ValueError):
        incident.resolve(
            "analyst1",
            "Investigation completed"
        )