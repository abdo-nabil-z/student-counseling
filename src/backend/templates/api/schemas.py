from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiTypes
from rest_framework import serializers

from consultation_backend.api_serializers import APIErrorResponseSerializer
from templates.api.serializers import (
    TemplateSerializer,
    CounselorRenderSerializer,
    StudentRenderSerializer,
    StudentCounselorRenderSerializer,
    ExternalRecipientRenderSerializer,
)

# ── Shared response fragments ────────────────────────────────────────────────


_render_success = inline_serializer(
    name="RenderSuccess",
    fields={"rendered": serializers.CharField()},
)


def _render_schema(request_serializer_class, description):
    return extend_schema(
        request=request_serializer_class,
        responses={
            200: _render_success,
            400: APIErrorResponseSerializer,
            404: APIErrorResponseSerializer,
            422: APIErrorResponseSerializer,
            501: APIErrorResponseSerializer,
        },
        description=description,
    )


def _pdf_render_schema(request_serializer_class, description):
    return extend_schema(
        request=request_serializer_class,
        responses={
            (200, "application/pdf"): OpenApiTypes.BINARY,
            400: APIErrorResponseSerializer,
            404: APIErrorResponseSerializer,
            422: APIErrorResponseSerializer,
            501: APIErrorResponseSerializer,
        },
        description=description,
    )


# ── Template CRUD ────────────────────────────────────────────────────────────

list_templates = extend_schema(
    request=None,
    responses={200: TemplateSerializer(many=True)},
    description="List all templates — one per purpose.",
)

get_template = extend_schema(
    request=None,
    responses={
        200: TemplateSerializer,
        404: APIErrorResponseSerializer,
    },
    description="Get the template for a specific purpose.",
)

update_template = extend_schema(
    request={"text/plain": OpenApiTypes.BINARY},
    responses={
        200: TemplateSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Update the content of the template for a specific purpose. "
        "Send the raw template text as the request body (UTF-8 bytestream), "
    ),
)

# ── Context schema (dev tooling) ─────────────────────────────────────────────

purpose_context_schema = extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            name="ContextSchemaResponse",
            fields={
                "path": serializers.CharField(),
                "type": serializers.CharField(),
                "directive": serializers.CharField(),
                "description": serializers.CharField(),
            },
            many=True,
        ),
        404: APIErrorResponseSerializer,
    },
    description=(
        "Return a flat list of available template variables for a purpose. "
        "Each entry has a dotted path, its type, a ready-to-paste directive, "
        "and a description of how to use it. "
        "Classical variables use {{path}}, lists use a for/endfor block, "
        "and list-element variables use {{elem.field}} for use inside a loop."
    ),
)

# ── Render endpoints ─────────────────────────────────────────────────────────

render_testmail = _render_schema(
    CounselorRenderSerializer,
    "Render the testmail template for a counselor, injecting their available slots.",
)

render_student_invitation = _render_schema(
    StudentRenderSerializer,
    "Render the student invitation email template for a student.",
)

render_student_reminder = _render_schema(
    StudentRenderSerializer,
    "Render the student reminder email template for a student.",
)

render_forced_appointment_assignment = _render_schema(
    StudentCounselorRenderSerializer,
    "Render the forced appointment assignment email template.",
)

render_appointment_invitation = _render_schema(
    StudentCounselorRenderSerializer,
    "Render the appointment invitation email template.",
)

render_counselor_preparation_instruction = _render_schema(
    StudentCounselorRenderSerializer,
    "Render the counselor preparation instruction email template.",
)

render_appointment_cancellation = _render_schema(
    StudentCounselorRenderSerializer,
    "Render the appointment cancellation email template.",
)

render_study_plan = _pdf_render_schema(
    StudentRenderSerializer,
    "Render the study_plan template into a PDF.",
)

render_appointment_minutes = _pdf_render_schema(
    StudentCounselorRenderSerializer,
    "Render the appointment_minutes template into a PDF.",
)

render_counselor_availability_request = (
    _render_schema(
        CounselorRenderSerializer,
        (
            "Render the counselor availability "
            "request email template."
        ),
    )
)

render_counselor_appointments_summary = (
    _render_schema(
        CounselorRenderSerializer,
        (
            "Render the accepted appointments "
            "summary email for a counselor."
        ),
    )
)


render_general_mail = _render_schema(
    ExternalRecipientRenderSerializer,
    "Render the general email template for an external recipient.",
)