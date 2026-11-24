
from exceptions import InvalidIncidentIdError
from models import IncidentIdResult


class IncidentIdGenerator:

    PREFIX = "INC-"

    def next_id(self, existing_ids: list[str]) -> IncidentIdResult:
        if not existing_ids:
            return IncidentIdResult(
                next_id="INC-001",
                missing_ids=[]
            )

        numbers = []

        for incident_id in existing_ids:
            if (
                not incident_id.startswith(self.PREFIX)
                or len(incident_id) != 7
                or not incident_id[4:].isdigit()
            ):
                raise InvalidIncidentIdError(
                    f"Invalid incident ID: {incident_id}"
                )

            numbers.append(int(incident_id[4:]))

        highest = max(numbers)

        missing_numbers = [
            number
            for number in range(1, highest)
            if number not in numbers
        ]

        missing_ids = [
            f"{self.PREFIX}{number:03}"
            for number in missing_numbers
        ]

        return IncidentIdResult(
            next_id=f"{self.PREFIX}{highest + 1:03}",
            missing_ids=missing_ids
        )
        