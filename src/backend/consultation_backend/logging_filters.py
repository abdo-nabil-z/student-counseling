import logging

from consultation_backend.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """
    Add the current request ID to every log record.

    Log records created outside a request receive "-" as their request ID.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
