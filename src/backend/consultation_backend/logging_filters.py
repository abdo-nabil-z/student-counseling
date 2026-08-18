import logging

from consultation_backend.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """
    Add the current request ID to every log record.

    Django request logs may be emitted after the request context has
    already been reset. In that case, use the request object attached
    to the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        request = getattr(record, "request", None)
        request_id = getattr(request, "request_id", None)

        record.request_id = (request_id or get_request_id())

        return True
