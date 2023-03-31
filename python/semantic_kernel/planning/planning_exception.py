from enum import Enum


class PlanningErrorCode(Enum):
    UNKNOWN_ERROR = -1
    INVALID_PLAN = 0
    INVALID_CONFIGURATION = 1


class PlanningException(Exception):
    def __init__(
        self,
        error_code: PlanningErrorCode,
        message: str = None,
    ):
        self.error_code = error_code
        self.message = message or self._get_default_message(error_code)
        super().__init__(self.message)

    def _get_default_message(self, error_code: PlanningErrorCode) -> str:
        if error_code == PlanningErrorCode.INVALID_PLAN:
            return "Invalid plan"
        elif error_code == PlanningErrorCode.INVALID_CONFIGURATION:
            return "Invalid configuration"
        else:
            return "Unknown error"
