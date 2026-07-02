from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from templates.api.serializers import (
    TemplateSerializer,
    CounselorRenderSerializer,
    StudentRenderSerializer,
    StudentCounselorRenderSerializer,
)

# ── Shared response fragments ────────────────────────────────────────────────

_render_error_detail = inline_serializer(
    name="TemplateRenderErrorDetail",
    fields={
        "type": serializers.ChoiceField(choices=["syntax_error", "undefined_variable"]),
        "message": serializers.CharField(),
        "line": serializers.IntegerField(required=False, help_text="Line number (syntax errors only)"),
        "variable": serializers.CharField(required=False, help_text="Variable name (undefined variable errors only)"),
    },
)

_render_success = inline_serializer(
    name="RenderSuccess",
    fields={"rendered": serializers.CharField()},
)

_render_400 = inline_serializer(
    name="RenderError400",
    fields={"error": serializers.CharField()},
)

_render_422 = inline_serializer(
    name="RenderError422",
    fields={"error": _render_error_detail},
)

_not_found = inline_serializer(
    name="NotFound",
    fields={"error": serializers.CharField()},
)


def _render_schema(request_serializer_class, description):
    return extend_schema(
        request=request_serializer_class,
        responses={
            200: _render_success,
            400: _render_400,
            404: _not_found,
            422: _render_422,
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
        404: _not_found,
    },
    description="Get the template for a specific purpose.",
)

update_template = extend_schema(
    request=TemplateSerializer,
    responses={
        200: TemplateSerializer,
        400: inline_serializer(name="UpdateTemplateError400", fields={"error": serializers.CharField()}),
        404: _not_found,
    },
    description="Update the content of the template for a specific purpose.",
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
        404: _not_found,
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

render_study_plan = _render_schema(
    StudentRenderSerializer,
    "Render the study plan document template for a student.",
)

render_appointment_minutes = _render_schema(
    StudentCounselorRenderSerializer,
    "Render the appointment minutes document template.",
)
