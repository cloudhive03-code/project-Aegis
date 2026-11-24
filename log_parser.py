
from exceptions import LogParseError
from models import ParsedLog


class LogParser:
    def parse(self, log: str) -> ParsedLog:
        words = log.split()
        if len(words) < 7:
            raise LogParseError("Log does not contain a username.")
        if "user" not in words:
            raise LogParseError("Log does not contain a username")
        try:
            time = words[0] + " " + words[1]
            severity = words[2].replace(":", "")
            user_index = words.index("user")
            username = words[user_index + 1]
            ip = words[-1]
        except (IndexError, ValueError) as error:
            raise LogParseError("Log format is invalid.") from error
        return ParsedLog(
            time = time,
            severity = severity,
            username = username,
            ip = ip
        )
