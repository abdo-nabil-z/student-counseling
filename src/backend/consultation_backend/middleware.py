from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from consultation_backend.request_context import (
    reset_request_id,
    set_request_id,
)


class RequestIdMiddleware:
    """
    Assign a unique identifier to every HTTP request.

    The identifier is:

    - available as request.request_id
    - added to every response as X-Request-ID
    - included in application logs
    - included in API error responses
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid4())
        request.request_id = request_id

        token = set_request_id(request_id)

        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)
