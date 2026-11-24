
from audit import ConsoleAuditLogger
from exceptions import NotificationError
from incident import Incident
from incident_id import IncidentIdGenerator
from log_parser import LogParser
from models import IncidentIdGap, IncidentIdResult
from threat import ThreatIntelligence


class AegisService:

    def __init__(
        self,
        repository,
        alert_service,
        parser=None,
        id_generator=None,
        audit_logger=None,
        gap_notifier=None
    ):
        self.repository = repository
        self.alert_service = alert_service
        self.parser = parser or LogParser()
        self.id_generator = id_generator or IncidentIdGenerator()
        self.audit_logger = audit_logger or ConsoleAuditLogger()
        self.gap_notifier = gap_notifier
    def process_log(self, log, incident_id):
        parsed_log = self.parser.parse(log)

        if self.repository.get_by_id(incident_id) is not None:
            raise ValueError(
                f"Incident {incident_id} already exists"
            )

        incident = Incident(
            incident_id,
            parsed_log.time,
            parsed_log.severity,
            parsed_log.username,
            parsed_log.ip
        )
        threat = ThreatIntelligence.check_ip(parsed_log.ip)
        incident.apply_threat_intelligence(threat)
        self.repository.save(incident)
        if incident.action == "Escalate":
            self.alert_service.notify(incident)
        return incident
    
    def next_incident_id(self) -> str:
        result = self.check_incident_id_sequence()
        if result.missing_ids:
            self.audit_logger.record("Incident ID sequence gap detected: " + ",".join(result.missing_ids))
        return result.next_id
    
    def process_logs(self, logs: list[str]) -> list[Incident]:
        incidents = []

        for log in logs:
            incident = self.process_log(
                log,
                self.next_incident_id()
            )
            incidents.append(incident)

        return incidents
    
    def update_incident_status(
        self,
        incident_id: str,
        new_status: str
    ) -> None:

        incident = self.repository.get_by_id(incident_id)

        if incident is None:
            raise ValueError(
                f"Incident {incident_id} not found."
            )

        incident.update_status(new_status)

        self.repository.update(
            incident_id,
            {"status": incident.status}
        )
        
    def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> Incident:

        incident = self.repository.get_by_id(incident_id)

        if incident is None:
            raise ValueError(
                f"Incident {incident_id} not found"
            )

        incident.resolve(
            resolved_by,
            resolution_notes
        )

        self.repository.update(
            incident_id,
            incident.to_dict()
        )

        return incident
    
    def generate_incident_id(self) -> IncidentIdResult:
        incidents = self.repository.load()

        existing_ids = [
            incident["id"]
            for incident in incidents
        ]

        return self.id_generator.next_id(existing_ids)
    
    def check_incident_id_sequence(self) -> IncidentIdResult:
        incidents = self.repository.load()

        existing_ids = [
            incident["id"]
            for incident in incidents
        ]

        return self.id_generator.next_id(existing_ids)
    
    def detect_incident_id_gap(self) -> IncidentIdGap | None:
        result = self.check_incident_id_sequence()

        if not result.missing_ids:
            return None
        gap = IncidentIdGap(missing_ids=result.missing_ids)
        self.audit_logger.record("Incident ID sequence gap detected: " + ",".join(gap.missing_ids))
        if self.gap_notifier is not None:
            try:
                self.gap_notifier.notify(gap)
            except NotificationError as error:
                self.audit_logger.record("Gap notification failed:" + str(error))
        return gap
        
        
    