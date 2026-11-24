
import pytest
from exceptions import NotificationError
from notification_retry import NotificationRetryExecutor, NotificationRetryPolicy


class AlwaysFailSender:
    def __init__(self):
        self.attempts = 0

    def send(self, message):
        self.attempts += 1
        raise NotificationError("Permanent failure")
    
class FailThreeTimesSender:
    def __init__(self):
        self.attempts = 0

    def send(self, message):
        self.attempts += 1

        if self.attempts <= 3:
            raise NotificationError("Temporary failure")
    
class FailOnceSender:
    def __init__(self):
        self.attempts = 0

    def send(self, message):
        self.attempts += 1

        if self.attempts == 1:
            raise NotificationError("Temporary failure")

class UnexpectedErrorSender:
    def __init__(self):
        self.attempts = 0

    def send(self, message):
        self.attempts += 1
        raise TypeError("Programming error")

def test_fail_once_sender_fails_first_attempt():
    sender = FailOnceSender()

    with pytest.raises(NotificationError, match="Temporary failure"):
        sender.send("Test notification")
    assert sender.attempts == 1
def test_retry_policy_delay_increases():
    policy = NotificationRetryPolicy(
        max_attempts=10,
        initial_delay=1,
        backoff_factor=2
    )

    assert policy.delay_for_attempt(1) == 1
    assert policy.delay_for_attempt(2) == 2
    assert policy.delay_for_attempt(3) == 4
    assert policy.delay_for_attempt(4) == 8


def test_retry_policy_rejects_zero_attempts():
    with pytest.raises(ValueError):
        NotificationRetryPolicy(max_attempts=0)


def test_retry_policy_rejects_negative_delay():
    with pytest.raises(ValueError):
        NotificationRetryPolicy(initial_delay=-1)


def test_retry_policy_rejects_invalid_backoff_factor():
    with pytest.raises(ValueError):
        NotificationRetryPolicy(backoff_factor=0)


def test_retry_policy_rejects_zero_attempt_number():
    policy = NotificationRetryPolicy(max_attempts=3)

    with pytest.raises(ValueError):
        policy.delay_for_attempt(0)
        
def test_retry_policy_rejects_attempt_beyond_maximum():
    policy = NotificationRetryPolicy(max_attempts=3)

    with pytest.raises(ValueError):
        policy.delay_for_attempt(4)
        
class FakeSender:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)
        
def test_retry_executor_sends_message():
    sender = FakeSender()
    policy = NotificationRetryPolicy(max_attempts=3)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=lambda delay: None
    )

    executor.send("Test notification")

    assert sender.messages == ["Test notification"]
    
def test_retry_executor_retries_after_failure():
    sender = FailOnceSender()
    policy = NotificationRetryPolicy(
        max_attempts=2,
        initial_delay=1,
        backoff_factor=2
    )

    delays = []

    def fake_delay(delay):
        delays.append(delay)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=fake_delay
    )

    executor.send("Test notification")

    assert sender.attempts == 2
    assert delays == [1]
    
def test_retry_executor_raises_after_max_attempts():
    sender = AlwaysFailSender()

    policy = NotificationRetryPolicy(
        max_attempts=3,
        initial_delay=1,
        backoff_factor=2
    )

    delays = []

    def fake_delay(delay):
        delays.append(delay)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=fake_delay
    )

    with pytest.raises(NotificationError, match="Permanent failure"):
        executor.send("Test notification")

    assert sender.attempts == 3
    assert delays == [1, 2]
    
def test_retry_executor_uses_exponential_backoff():
    sender = FailThreeTimesSender()

    policy = NotificationRetryPolicy(
        max_attempts=4,
        initial_delay=1,
        backoff_factor=2
    )

    delays = []

    def fake_delay(delay):
        delays.append(delay)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=fake_delay
    )

    executor.send("Test notification")

    assert sender.attempts == 4
    assert delays == [1, 2, 4]
    
def test_retry_executor_does_not_retry_unexpected_exception():
    sender = UnexpectedErrorSender()
    policy = NotificationRetryPolicy(
        max_attempts=3,
        initial_delay=1,
        backoff_factor=2
    )

    delays = []

    def fake_delay(delay):
        delays.append(delay)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=fake_delay
    )

    with pytest.raises(TypeError, match="Programming error"):
        executor.send("Test notification")

    assert sender.attempts == 1
    assert delays == []
    
def test_retry_executor_returns_success_result():
    sender = FakeSender()
    policy = NotificationRetryPolicy(max_attempts=3)

    executor = NotificationRetryExecutor(
        sender=sender,
        policy=policy,
        delay_function=lambda delay: None
    )

    result = executor.send("Test notification")

    assert result.attempts == 1
    assert result.success is True
    assert result.last_error is None