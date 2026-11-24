
from exceptions import LogParseError
from incident import Incident
from models import IngestionResult
from service import AegisService


class Aegis:

    def __init__(
        self,
        repository,
        alert_service,
        parser=None,
        id_generator=None,
        audit_logger=None,
        gap_notifier=None
    ) -> None:
        self.service = AegisService(
            repository=repository,
            alert_service=alert_service,
            parser=parser,
            id_generator=id_generator,
            audit_logger=audit_logger,
            gap_notifier=gap_notifier
        )
        
    def process_log(
        self,
        log: str,
        incident_id: str
    ) -> Incident:
        return self.service.process_log(
            log,
            incident_id
        )
        
    def _next_incident_id(self) -> str:
        return self.service.next_incident_id()

    def process_logs(
        self,
        logs: list[str]
    ) -> list[Incident]:
        return self.service.process_logs(logs)

    def update_incident_status(
        self,
        incident_id: str,
        new_status: str
    ) -> None:
        self.service.update_incident_status(
            incident_id,
            new_status
        )

    def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> Incident:
        return self.service.resolve_incident(
            incident_id,
            resolved_by,
            resolution_notes
        )
        
    def process_log_file(self, file_path: str) -> list[Incident]:
        with open(file_path, "r") as file:
            logs = [
                line.strip()
                for line in file
                if line.strip()
            ]

        return self.service.process_logs(logs)


    def process_log_file_safe(
        self,
        file_path: str
    ) -> IngestionResult:

        incidents = []
        invalid_logs = 0

        with open(file_path, "r") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    incident = self.service.process_log(
                        line.strip(),
                        self.service.next_incident_id()
                    )
                    incidents.append(incident)

                except LogParseError:
                    invalid_logs += 1

        return IngestionResult(
            incidents=incidents,
            invalid_logs=invalid_logs
        )