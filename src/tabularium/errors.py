class ReportError(Exception):
    pass


class ReportEmptyError(ReportError):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "No data available to build the report.")
