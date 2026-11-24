
import sys

from alert import AlertService, EmailAlert
from repos import JSONIncidentRepository

from aegis import Aegis


def list_incidents(repository):
    incidents = repository.load()

    if not incidents:
        print("No incidents found.")
        return

    print("Aegis Incidents")
    print("----------------")

    for incident in incidents:
        print(
            f"{incident['id']} | "
            f"{incident['severity']} | "
            f"{incident['user']} | "
            f"{incident['ip']} | "
            f"Score: {incident['score']} | "
            f"Status: {incident.get('status', 'Unknown')} | "
            f"Action: {incident['action']}"
        )
        
def get_incident(repository, incident_id):
    incident = repository.get_by_id(incident_id)

    if incident is None:
        print(f"Incident {incident_id} not found.")
        return

    print("Incident ID:", incident.id)
    print("Time:", incident.time)
    print("Severity:", incident.severity)
    print("User:", incident.user)
    print("IP:", incident.ip)
    print("Score:", incident.score)
    print("Status:", incident.status)
    print("Notes:", incident.notes)
    print("Action:", incident.action)

def main(repository=None, alert_service=None, file_path=None):

    if repository is None:
        repository = JSONIncidentRepository()

    if alert_service is None:
        alert = EmailAlert()
        alert_service = AlertService(alert)

    aegis = Aegis(
        repository=repository,
        alert_service=alert_service
    )

    if file_path:
        result = aegis.process_log_file_safe(file_path)

        print("Aegis Log Processing")
        print("--------------------")
        print("Processed:", len(result.incidents))
        print("Invalid:", result.invalid_logs)

        for incident in result.incidents:
            print(
                f"{incident.id} | "
                f"{incident.severity} | "
                f"{incident.user} | "
                f"{incident.ip} | "
                f"Score: {incident.score} | "
                f"Action: {incident.action}"
            )

        return result

    log = (
        "2026-08-15 16:24:37 WARNING: "
        "Failed login attempt for user jsmith "
        "from 192.168.1.50"
    )

    incident = aegis.process_log(
        log,
        "INC-001"
    )

    print("Incident ID:", incident.id)
    print("Time:", incident.time)
    print("Severity:", incident.severity)
    print("User:", incident.user)
    print("IP:", incident.ip)
    print("Score:", incident.score)
    print("Notes:", incident.notes)
    print("Action:", incident.action)

    return incident


if __name__ == "__main__":
    repository = JSONIncidentRepository()
    if len(sys.argv) == 3 and sys.argv[1] == "get":
        get_incident(repository, sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        list_incidents(repository)
    else:
        main()