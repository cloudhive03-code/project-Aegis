
from typing import ClassVar


class ThreatIntelligence:
    ip_watchlist: ClassVar[dict[str, dict[str, str | int]]] = {
        "192.168.1.50": {
            "risk": 15,
            "reason": "Multiple failed login attempts"
        },
        "10.0.0.5": {
            "risk": 20,
            "reason": "Known compromised host"
        },
        "192.168.10.45": {
            "risk": 15,
            "reason": "Known malicious IP"
        }
    }

    @classmethod
    def check_ip(
        cls,
        ip: str
    ) -> dict[str, str | int] | None:
        return cls.ip_watchlist.get(ip)


