
import pytest
from log_parser import LogParser
from exceptions import LogParseError

def test_pasrse_log():
    parser = LogParser()
    log = (
        "2026-08-15 16:24:37 WARNING: "
        "Failed login attempt for user jsmith "
        "from 192.168.10.45"
    )
    result = parser.parse(log)
    assert result.time == "2026-08-15 16:24:37"
    assert result.severity == "WARNING"
    assert result.username == "jsmith"
    assert result.ip == "192.168.10.45"
    
def test_invalid_log():
    parser = LogParser()
    bad_log = (
        "2026-08-15 16:24:37 "
        "WARNING: Failed login attempt"
    )
    with pytest.raises(LogParseError):
        parser.parse(bad_log)
        
def test_parse_valid_log():
    parser = LogParser()
    log = "2026-08-15 16:40:00 CRITICAL: failed login user admin 192.168.1.20"
    result = parser.parse(log)
    assert result.time == "2026-08-15 16:40:00"
    assert result.severity == "CRITICAL"
    assert result.username == "admin"
    assert result.ip == "192.168.1.20"
    
def test_parse_log_too_short():
    parser = LogParser()
    log = "2026-08-15 16:40:00"
    with pytest.raises(LogParseError):
        parser.parse(log)
        
def test_parse_invalid_log_without_user():
    parser = LogParser()
    log = "2026-08-15 16:40:00 CRITICAL: failed login admin 192.168.1.20"
    with pytest.raises(LogParseError):
        parser.parse(log)
        
#def test_parse_invalid_log_format():
#    parser = LogParser()
#    log = "2026-08-15 16:40:00 CRITICAL: failed login user"
#    with pytest.raises(LogParseError):
#        parser.parse(log)
        

def test_parse_invalid_log_format():
    parser = LogParser()

    log = "2026-08-29 15:30:00 CRITICAL: security event detected user"

    with pytest.raises(LogParseError, match="Log format is invalid."):
        parser.parse(log)