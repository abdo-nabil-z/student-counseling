from typing import Any

from rest_framework.exceptions import APIException


class ApplicationAPIException(APIException):
    """
    Base class for expected application errors that need structured details.
    """

    error_details: Any = None

    def __init__(self, *, message: str | None = None, code: str | None = None, details: Any = None) -> None:
        self.error_details = details

        super().__init__(detail=message, code=code)


class TemplateRenderFailed(ApplicationAPIException):
    status_code = 422
    default_detail = "The template could not be rendered."
    default_code = "template_render_error"


class TemplateContextNotImplemented(ApplicationAPIException):
    status_code = 501
    default_detail = "Template context generation is not implemented."
    default_code = "template_context_not_implemented"