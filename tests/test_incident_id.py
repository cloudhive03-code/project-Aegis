
import pytest
from exceptions import InvalidIncidentIdError
from incident_id import IncidentIdGenerator


def test_generates_first_incident_id():
    generator = IncidentIdGenerator()

    result = generator.next_id([])

    assert result.next_id == "INC-001"
    assert result.missing_ids == []


def test_generates_next_incident_id():
    generator = IncidentIdGenerator()

    result = generator.next_id([
        "INC-001",
        "INC-002"
    ])

    assert result.next_id == "INC-003"
    assert result.missing_ids == []


def test_detects_sequence_gaps():
    generator = IncidentIdGenerator()

    result = generator.next_id([
        "INC-001",
        "INC-002",
        "INC-005"
    ])

    assert result.next_id == "INC-006"
    assert result.missing_ids == [
        "INC-003",
        "INC-004"
    ]


def test_rejects_malformed_incident_id():
    generator = IncidentIdGenerator()

    with pytest.raises(
        InvalidIncidentIdError,
        match="Invalid incident ID: INC-BAD"
    ):
        generator.next_id([
            "INC-001",
            "INC-BAD",
            "INC-005"
        ])
        
def test_rejects_short_incident_id():
    generator = IncidentIdGenerator()

    with pytest.raises(
        InvalidIncidentIdError,
        match="Invalid incident ID: INC-1"
    ):
        generator.next_id(["INC-1"])


def test_rejects_two_digit_incident_id():
    generator = IncidentIdGenerator()

    with pytest.raises(
        InvalidIncidentIdError,
        match="Invalid incident ID: INC-01"
    ):
        generator.next_id(["INC-01"])


def test_rejects_four_digit_incident_id():
    generator = IncidentIdGenerator()

    with pytest.raises(
        InvalidIncidentIdError,
        match="Invalid incident ID: INC-0001"
    ):
        generator.next_id(["INC-0001"])