from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiTypes
from rest_framework import serializers

from consultation_backend.api_serializers import APIErrorResponseSerializer
from templates.api.serializers import TemplateSerializer

# ── Shared response fragments ────────────────────────────────────────────────


_render_success = inline_serializer(
    name="RenderSuccess",
    fields={"rendered": serializers.CharField()},
)


_render_purpose_request = inline_serializer(
    name="RenderPurposeRequest",
    fields={
        "counselor_id": serializers.IntegerField(required=False),
        "student_id": serializers.IntegerField(required=False),
        "appointment_id": serializers.IntegerField(required=False),
    },
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

# ── Render endpoint ──────────────────────────────────────────────────────────

render_purpose = extend_schema(
    request=_render_purpose_request,
    responses={
        200: _render_success,
        (200, "application/pdf"): OpenApiTypes.BINARY,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        422: APIErrorResponseSerializer,
        501: APIErrorResponseSerializer,
    },
    description=(
        "Render the template for the given purpose. Returns JSON "
        '`{"rendered": ...}` for email purposes, or a PDF binary for document '
        "purposes (study_plan, appointment_minutes).\n\n"
        "Required fields by purpose:\n"
        "- counselor_id only: counselor_availability_request, "
        "counselor_appointments_summary\n"
        "- student_id only: student_invitation, student_reminder, study_plan\n"
        "- student_id + counselor_id + appointment_id: "
        "forced_appointment_assignment, appointment_invitation, "
        "counselor_preparation_instruction, appointment_cancellation, "
        "appointment_minutes\n"
        "- recipient_email only: general_mail\n\n"
    ),
)