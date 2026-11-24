
from dataclasses import dataclass

from incident import Incident


@dataclass
class ParsedLog:
    time: str
    severity: str
    username: str
    ip: str
    
@dataclass
class IngestionResult:
    incidents: list[Incident]
    invalid_logs: int
    
@dataclass
class IncidentIdResult:
    next_id: str
    missing_ids: list[str]
    
@dataclass
class IncidentIdGap:
    missing_ids: list[str]