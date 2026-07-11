from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.defaults import page_not_found, server_error

from consultation_backend.request_context import get_request_id


def _get_request_id(request: HttpRequest) -> str:
    return getattr(request, "request_id", get_request_id())


def api_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    Return JSON when an unknown /api/ route is requested.

    Non-API routes continue using Django's normal HTML 404 page.
    """
    if not request.path.startswith("/api/"):
        return page_not_found(request, exception)
    
    return JsonResponse(
        {
            "error": {
                "code": "not_found",
                "message": "The requested API endpoint was not found.",
                "details": None,
                "request_id": _get_request_id(request),
            }
        },
        status=404,
    )


def api_server_error(request: HttpRequest) -> HttpResponse:
    """
    Return a safe JSON response for errors occurring outside DRF.

    Non-API routes continue using Django's normal HTML 500 page.
    """
    if not request.path.startswith("/api/"):
        return server_error(request)

    return JsonResponse(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected server error occurred.",
                "details": None,
                "request_id": _get_request_id(request),
            }
        },
        status=500,
    )
