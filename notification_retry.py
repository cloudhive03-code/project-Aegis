
from dataclasses import dataclass

from exceptions import NotificationError


@dataclass
class RetryResult:
    attempts: int
    success: bool
    last_error: NotificationError | None = None
class NotificationRetryPolicy:
    def __init__(
        self,
        max_attempts: int = 10,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1"
            )

        if initial_delay < 0:
            raise ValueError(
                "initial_delay cannot be negative"
            )

        if backoff_factor < 1:
            raise ValueError(
                "backoff_factor must be at least 1"
            )

        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt < 1:
            raise ValueError(
                "attempt must be at least 1"
            )
        if attempt > self.max_attempts:
            raise ValueError("attempt cannot exceed max_attempts")
        return self.initial_delay * (
            self.backoff_factor ** (attempt - 1)
        )
        
class NotificationRetryExecutor:
    def __init__(
        self,
        sender,
        policy,
        delay_function
    ):
        self.sender = sender
        self.policy = policy
        self.delay_function = delay_function

    def send(self, message):
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                self.sender.send(message)
                return RetryResult(
                    attempts=attempt,
                    success=True
                )

            except NotificationError:
                if attempt == self.policy.max_attempts:
                    raise

                delay = self.policy.delay_for_attempt(attempt)
                self.delay_function(delay)