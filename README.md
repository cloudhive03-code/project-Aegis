
# Project Aegis

**A Modular Python-Based Security Incident Management and Analysis System**

## 1. Overview

Project Aegis is a Python-based cybersecurity learning and engineering project designed to process security logs, identify potentially suspicious activity, create security incidents, assess threat risk, and support incident management.

The project is being developed as a modular application with an emphasis on clean architecture, testability, maintainability, and secure software engineering practices.

Aegis is also the foundation of a broader cybersecurity laboratory focused on detection engineering, security monitoring, incident response, and defensive security operations.

## 2. Project Objectives

- Parse and process security log entries.
- Generate unique incident identifiers.
- Identify known suspicious IP addresses through threat intelligence checks.
- Assign risk scores and recommended actions.
- Persist incident records.
- Manage incident status and resolution.
- Generate notifications for incidents requiring escalation.
- Detect gaps in incident ID sequences.
- Build a testable foundation for future SIEM integration.

## 3. Current Architecture

Aegis uses a modular design that separates application responsibilities.

| Module | Responsibility |
|---|---|
| `aegis.py` | Application facade |
| `service.py` | Core incident-processing logic |
| `incident.py` | Incident model and lifecycle |
| `log_parser.py` | Security log parsing |
| `threat.py` | Threat intelligence checks |
| `incident_id.py` | Incident ID generation |
| `repos.py` | JSON incident persistence |
| `alert.py` | Notification services |
| `audit.py` | Audit logging |
| `notification_retry.py` | Notification retry mechanisms |
| `models.py` | Supporting data models |
| `exceptions.py` | Application exceptions |
| `main.py` | Application entry point and CLI |

## 4. Incident Processing Workflow

The current processing workflow follows this sequence:

1. Receive a security log.
2. Parse the log into structured data.
3. Check for an existing incident ID.
4. Create an incident.
5. Perform a threat intelligence check.
6. Apply threat intelligence results and risk assessment.
7. Persist the incident.
8. Trigger a notification when escalation is required.

## 5. Technology Stack

- Python 3.14.3 (current development environment)
- pytest 9.2.0
- coverage.py 7.17.5
- JSON-based persistence
- Git and GitHub for version control and project documentation

## 6. Testing and Quality Assurance

Aegis uses pytest for automated testing and coverage.py to measure executed application code.

**Latest development checkpoint:**

| Metric | Result |
|---|---:|
| Automated tests passing | 103 |
| Total statement coverage | 99% |
| `service.py` coverage | 100% |
| `main.py` coverage | 100% |

Run the test suite:

```bash
python -m pytest -q
```

Run coverage:

```bash
python -m coverage run --omit="tests/*" -m pytest -q
python -m coverage report -m
```

These results represent the current development checkpoint and may change as the application evolves.

## 7. Project Structure

```text
Aegis/
│
├── aegis.py
├── alert.py
├── audit.py
├── exceptions.py
├── incident.py
├── incident_id.py
├── log_parser.py
├── main.py
├── models.py
├── notification_retry.py
├── repos.py
├── service.py
├── threat.py
│
└── tests/
    ├── test_aegis.py
    ├── test_aegis_integration.py
    ├── test_alert.py
    ├── test_incident.py
    ├── test_incident_id.py
    ├── test_log_parser.py
    ├── test_main.py
    ├── test_notification_retry.py
    ├── test_repos.py
    └── test_threat_intelligence.py
```

## 8. Development Roadmap

### Phase 1: Core Architecture
- Modular application structure.
- Incident creation and management.
- Log parsing.
- Threat intelligence integration.
- Repository and notification components.

### Phase 2: Testing and Hardening
- Automated unit and integration testing.
- Code coverage improvements.
- Input validation and error handling.
- Persistence reliability.
- Security-focused code review.

### Phase 3: Advanced Detection
- More sophisticated event detection.
- Detection rules and event correlation.
- Risk assessment improvements.
- Suspicious activity analysis.

### Phase 4: SIEM Integration
- Integration with Splunk.
- Security event forwarding.
- Detection and alert correlation.

### Phase 5: Blue Team Operations
- Monitoring workflows.
- Alert investigation.
- Incident response procedures.
- Security reporting.

### Phase 6: Purple Team Simulation
- Controlled security simulations.
- Detection validation.
- Defensive improvement and evaluation.

## 9. Security and Development Philosophy

Aegis is being developed with the following engineering principles:

- Separation of concerns.
- Focused and reusable components.
- Dependency injection where appropriate.
- Automated testing.
- Explicit error handling.
- Secure-by-design development.
- Maintainable and documented code.

## 10. Project Status

**Current status:** Active development.

Aegis is an evolving cybersecurity engineering project. Features and architecture will continue to be tested, reviewed, and improved as development progresses.

This project is intended for educational and authorized defensive security use.
