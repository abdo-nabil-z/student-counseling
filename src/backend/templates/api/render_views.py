from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BaseRenderer, JSONRenderer
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
)
from templates.context_registry import (
    TestmailContext,
    StudentAndBlocksContext,
    AppointmentStudentCounselorContext,
    CounselorOnlyContext,
    CounselorAppointmentsContext,
    StudyPlanContext,
    AppointmentMinutesContext,
)
from templates.rendering import TemplateRenderError, render_from_template  # noqa: F401 — re-exported
from pdf.rendering import render_template_to_pdf

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


@schemas.render_testmail
@api_view(["POST"])
def render_testmail(request):
    return _render_purpose(request, Purpose.TESTMAIL, CounselorRenderSerializer, TestmailContext)


@schemas.render_student_invitation
@api_view(["POST"])
def render_student_invitation(request):
    return _render_purpose(request, Purpose.STUDENT_INVITATION_MAIL, StudentRenderSerializer, StudentAndBlocksContext)


@schemas.render_student_reminder
@api_view(["POST"])
def render_student_reminder(request):
    return _render_purpose(request, Purpose.STUDENT_REMINDER_MAIL, StudentRenderSerializer, StudentAndBlocksContext)


@schemas.render_forced_appointment_assignment
@api_view(["POST"])
def render_forced_appointment_assignment(request):
    return _render_purpose(request, Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_appointment_invitation
@api_view(["POST"])
def render_appointment_invitation(request):
    return _render_purpose(request, Purpose.APPOINTMENT_INVITATION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_counselor_preparation_instruction
@api_view(["POST"])
def render_counselor_preparation_instruction(request):
    return _render_purpose(request, Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_appointment_cancellation
@api_view(["POST"])
def render_appointment_cancellation(request):
    return _render_purpose(request, Purpose.APPOINTMENT_CANCELLATION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_study_plan
@api_view(["POST"])
@renderer_classes([PDFRenderer, JSONRenderer])
def render_study_plan(request):
    return _render_pdf_purpose(request, Purpose.STUDY_PLAN, StudentRenderSerializer, StudyPlanContext)


@schemas.render_appointment_minutes
@api_view(["POST"])
@renderer_classes([PDFRenderer, JSONRenderer])
def render_appointment_minutes(request):
    return _render_pdf_purpose(request, Purpose.APPOINTMENT_MINUTES, StudentCounselorRenderSerializer, AppointmentMinutesContext)


@schemas.render_counselor_availability_request
@api_view(["POST"])
def render_counselor_availability_request(request):
    return _render_purpose(
        request,
        Purpose.COUNSELOR_AVAILABILITY_REQUEST_MAIL,
        CounselorRenderSerializer,
        CounselorOnlyContext,
    )


@schemas.render_counselor_appointments_summary
@api_view(["POST"])
def render_counselor_appointments_summary(request):
    return _render_purpose(
        request,
        Purpose.COUNSELOR_APPOINTMENTS_SUMMARY_MAIL,
        CounselorRenderSerializer,
        CounselorAppointmentsContext,
    )