
from threat import ThreatIntelligence


def test_known_malicious_ip():
    threat = ThreatIntelligence.check_ip("192.168.10.45")

    assert threat is not None
    assert threat["risk"] == 15


def test_unknown_ip():
    threat = ThreatIntelligence.check_ip("192.168.1.100")

    assert threat is None
    
    
