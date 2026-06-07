from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers

from templates.api.serializers import TemplateSerializer, TemplateRenderTestmailRequestSerializer


_error_str = inline_serializer(
    name="_ErrorStr", fields={"error": serializers.CharField()}
)

_render_error_detail = inline_serializer(
    name="TemplateRenderErrorDetail",
    fields={
        "type": serializers.ChoiceField(choices=["syntax_error", "undefined_variable"]),
        "message": serializers.CharField(),
        "line": serializers.IntegerField(required=False, help_text="Line number (syntax errors only)"),
        "variable": serializers.CharField(required=False, help_text="Variable name (undefined variable errors only)"),
    },
)

render_template_for_testmail = extend_schema(
    parameters=[
        OpenApiParameter(
            name="template_id", type=int, location=OpenApiParameter.QUERY,
            required=True, description="ID of the template to render",
        ),
    ],
    request=TemplateRenderTestmailRequestSerializer,
    responses={
        200: inline_serializer(name="TestmailRenderResponse", fields={"rendered": serializers.CharField()}),
        400: inline_serializer(name="TestmailError400", fields={"error": serializers.CharField()}),
        404: inline_serializer(name="TestmailError404", fields={"error": serializers.CharField()}),
        422: inline_serializer(name="TestmailError422", fields={"error": _render_error_detail}),
    },
    description="Render a testmail template for a counselor, injecting their available slots into the context",
)

templates_by_purpose = extend_schema(
    parameters=[
        OpenApiParameter(
            name="purpose", type=str, location=OpenApiParameter.QUERY,
            required=False, description="Filter templates by purpose key",
        ),
    ],
    request=None,
    responses={
        200: TemplateSerializer(many=True),
        400: inline_serializer(name="ErrorResponse", fields={"error": serializers.CharField()}),
    },
    description="Get templates, optionally filtered by purpose key",
)

create_template = extend_schema(
    request=TemplateSerializer,
    responses={
        201: TemplateSerializer,
        400: inline_serializer(name="CreateTemplateError400", fields={"error": serializers.CharField()}),
    },
    description="Create a new template",
)

update_template = extend_schema(
    request=TemplateSerializer,
    responses={
        200: TemplateSerializer,
        400: inline_serializer(name="UpdateTemplateError400", fields={"error": serializers.CharField()}),
        404: inline_serializer(name="UpdateTemplateError404", fields={"error": serializers.CharField()}),
    },
    description="Partially update an existing template",
)

delete_template = extend_schema(
    request=None,
    responses={
        204: None,
        404: inline_serializer(name="DeleteTemplateError404", fields={"error": serializers.CharField()}),
    },
    description="Delete a template by ID",
)

purposes_list = extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            name="PurposeListResponse",
            fields={
                "key": serializers.CharField(),
                "label": serializers.CharField(),
                "default_template_id": serializers.IntegerField(allow_null=True),
            },
            many=True,
        )
    },
    description="List all available purpose keys with their current default template",
)

purpose_context_schema = extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            name="ContextSchemaResponse",
            fields={
                "path": serializers.CharField(),
                "type": serializers.CharField(),
                "description": serializers.CharField(required=False),
            },
            many=True,
        ),
        404: inline_serializer(name="ContextSchemaError404", fields={"error": serializers.CharField()}),
    },
    description=(
        "Return a flat list of available template variables for a purpose. "
        "Each entry has a dotted path (e.g. counselor.first_name), its type, "
        "and an optional description. Array items appear as path[].field."
    ),
)

set_default_template = extend_schema(
    request=inline_serializer(
        name="SetDefaultTemplateRequest",
        fields={"template_id": serializers.IntegerField()},
    ),
    responses={
        204: None,
        400: inline_serializer(name="SetDefaultError400", fields={"error": serializers.CharField()}),
    },
    description="Set the default template for a purpose",
)
