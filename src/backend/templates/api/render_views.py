from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.exceptions import NotFound
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

import logging

from consultation_backend.api_exceptions import (
    TemplateContextNotImplemented,
    TemplateRenderFailed,
    PdfGenerationFailed,
)
from templates.models import Template, Purpose
from templates.api import schemas
from templates.api.serializers import (
    CounselorRenderSerializer,
    StudentRenderSerializer,
    StudentCounselorRenderSerializer,
    ExternalRecipientRenderSerializer,
)
from templates.context_registry import PURPOSE_CONTEXT_REGISTRY, PDFContext
from templates.rendering import TemplateRenderError, render_from_template  # noqa: F401 — re-exported
from pdf.rendering import render_template_to_pdf

# Which request serializer a purpose needs, keyed the same as PURPOSE_CONTEXT_REGISTRY.
PURPOSE_SERIALIZER_REGISTRY: dict[str, type] = {
    Purpose.STUDENT_INVITATION_MAIL: StudentRenderSerializer,
    Purpose.STUDENT_REMINDER_MAIL: StudentRenderSerializer,
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: StudentCounselorRenderSerializer,
    Purpose.APPOINTMENT_INVITATION_MAIL: StudentCounselorRenderSerializer,
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: StudentCounselorRenderSerializer,
    Purpose.APPOINTMENT_CANCELLATION_MAIL: StudentCounselorRenderSerializer,
    Purpose.STUDY_PLAN: StudentRenderSerializer,
    Purpose.APPOINTMENT_MINUTES: StudentCounselorRenderSerializer,
    Purpose.COUNSELOR_AVAILABILITY_REQUEST_MAIL: CounselorRenderSerializer,
    Purpose.COUNSELOR_APPOINTMENTS_SUMMARY_MAIL: CounselorRenderSerializer,
    Purpose.GENERAL_MAIL: ExternalRecipientRenderSerializer,
}

logger = logging.getLogger(__name__)


class PDFRenderer(BaseRenderer):
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


def _render_purpose(request, purpose, serializer_class, context_class):
    template = get_object_or_404(Template, purpose=purpose)
    serializer = serializer_class(data=request.data)

    serializer.is_valid(raise_exception=True)

    try:
        ctx = context_class.build(**serializer.validated_data)

    except NotImplementedError as exc:
        raise TemplateContextNotImplemented(
            details={
                "purpose": purpose,
            }
        ) from exc
    
    try:
        rendered = render_from_template(template.content, **ctx.model_dump())
    
    except TemplateRenderError as exc:
        raise TemplateRenderFailed(
            details=exc.to_dict()
        ) from exc

    return Response({"rendered": rendered}, status=status.HTTP_200_OK)


def _render_pdf_purpose(request, purpose, serializer_class, context_class):
    template = get_object_or_404(Template, purpose=purpose)
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        ctx = context_class.build(**serializer.validated_data)
    except NotImplementedError as exc:
        raise TemplateContextNotImplemented(details={"purpose": purpose}) from exc

    try:
        pdf_bytes = render_template_to_pdf(template.content, **ctx.model_dump())
    except TemplateRenderError as exc:
        raise TemplateRenderFailed(details=exc.to_dict()) from exc
    except Exception as exc:
        logger.exception("PDF generation failed for purpose=%s", purpose)
        raise PdfGenerationFailed(details={"purpose": purpose}) from exc

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{purpose}.pdf"'
    return response


@schemas.render_purpose
@api_view(["POST"])
@renderer_classes([JSONRenderer, PDFRenderer])
def render_purpose(request, purpose):
    if purpose not in PURPOSE_CONTEXT_REGISTRY:
        raise NotFound(
            detail=f"Unknown template purpose '{purpose}'.",
            code="unknown_template_purpose",
        )

    context_class = PURPOSE_CONTEXT_REGISTRY[purpose]
    serializer_class = PURPOSE_SERIALIZER_REGISTRY[purpose]

    if issubclass(context_class, PDFContext):
        return _render_pdf_purpose(request, purpose, serializer_class, context_class)
    return _render_purpose(request, purpose, serializer_class, context_class)