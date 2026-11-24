
from typing import Protocol


class AuditLogger(Protocol):
    def record(self, message: str) -> None:
        ...
        
class ConsoleAuditLogger:
    def record(self, message: str) -> None:
        print(f"Audit: {message}")