import logging
from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from django.http import Http404

from consultation_backend.api_exceptions import ApplicationAPIException


logger = logging.getLogger(__name__)


STATUS_ERROR_CODES = {
    400: "bad_request",
    401: "authentication_failed",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    415: "unsupported_media_type",
    422: "unprocessable_entity",
    429: "throttled",
}


def _get_request_id(context: dict[str, Any]) -> str:
    request = context.get("request")

    if request is None:
        return "-"

    return getattr(request, "request_id", "-")


def _get_request_information(context: dict[str, Any]) -> dict[str, str]:
    request = context.get("request")

    if request is None:
        return {
            "request_method": "-",
            "request_path": "-",
        }

    return {
        "request_method": request.method,
        "request_path": request.path,
    }


def _get_error_code(exception: Exception, response: Response) -> str:
    if isinstance(exception, ValidationError):
        return "validation_error"

    if isinstance(exception, Http404):
        return "resource_not_found"
    
    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        detail_code = getattr(detail, "code", None)

        if detail_code:
            return str(detail_code)

    return STATUS_ERROR_CODES.get(response.status_code, "api_error")


def _get_error_message(exception: Exception, response: Response) -> str:
    if isinstance(exception, ValidationError):
        return "The submitted data is invalid."

    if isinstance(exception, Http404):
        return (
            "The requested resource does not exist."
        )
    
    if isinstance(response.data, dict):
        detail = response.data.get("detail")

        if detail is not None:
            return str(detail)

    return response.status_text or "The request could not be completed."


def _get_error_details(exception: Exception, response: Response) -> Any:
    if isinstance(exception, ApplicationAPIException):
        return exception.error_details
    
    if isinstance(exception, ValidationError):
        return response.data

    if (isinstance(response.data, dict) and set(response.data.keys()) == {"detail"}):
        return None

    return response.data


def custom_exception_handler(exception: Exception, context: dict[str, Any]) -> Response:
    """
    Convert DRF and Django exceptions into a consistent API response.

    Expected API exceptions are handled by DRF first.

    Unexpected exceptions are logged with their complete traceback and
    returned to the client as a safe generic 500 response.
    """
    response = drf_exception_handler(exception, context)
    request_id = _get_request_id(context)
    request_information = _get_request_information(context)

    if response is None:
        logger.exception(
            "Unhandled API exception",
            extra=request_information,)

        return Response(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected server error occurred.",
                    "details": None,
                    "request_id": request_id,
                }
            },
            status=500,
        )

    if response.status_code >= 500 and not isinstance(exception, ApplicationAPIException):
        logger.exception(
            "API exception returned a server error",
            extra=request_information,
        )

    response.data = {
        "error": {
            "code": _get_error_code(exception, response),
            "message": _get_error_message(exception, response),
            "details": _get_error_details(exception, response),
            "request_id": request_id,
        }
    }

    return response
