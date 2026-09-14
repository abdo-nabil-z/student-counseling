from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound, ParseError

from consultation_backend.api_serializers import APIErrorResponseSerializer
from templates.models import Template, Purpose
from templates.api.serializers import TemplateSerializer
from templates.api import schemas
from templates.context_registry import PURPOSE_CONTEXT_REGISTRY, PDFContext, flatten_context_schema, annotate_directives
from templates.rendering import FORM_FIELD_ELEMENTS
from templates.api.render_views import (  # noqa: F401 — re-exported for urls.py
    render_testmail,
    render_student_invitation,
    render_student_reminder,
    render_forced_appointment_assignment,
    render_appointment_invitation,
    render_counselor_preparation_instruction,
    render_appointment_cancellation,
    render_study_plan,
    render_appointment_minutes,
)


@schemas.list_templates
@api_view(["GET"])
def list_templates(request):
    existing = {t.purpose: t for t in Template.objects.all()}
    templates = [existing.get(p) or Template(purpose=p, content="") for p in Purpose.values]
    serializer = TemplateSerializer(templates, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@schemas.get_template
@api_view(["GET"])
def get_template(request, purpose):
    if purpose not in Purpose.values:
        raise NotFound(
            detail=f"Unknown template purpose '{purpose}'.",
            code="unknown_template_purpose",
        )
    template = Template.objects.filter(purpose=purpose).first() or Template(purpose=purpose, content="")
    return Response(TemplateSerializer(template).data, status=status.HTTP_200_OK)


@schemas.update_template
@api_view(["PUT"])
def update_template(request, purpose):
    if purpose not in Purpose.values:
        raise NotFound(
            detail=f"Unknown template purpose '{purpose}'.",
            code="unknown_template_purpose",
        )

    try:
        content = request.body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ParseError(detail="Request body must be valid UTF-8 text.") from exc

    template, _ = Template.objects.get_or_create(purpose=purpose)
    template.content = content
    template.save()

    return Response(
        TemplateSerializer(template).data,
        status=status.HTTP_200_OK,
    )


@schemas.purpose_context_schema
@api_view(["GET"])
def purpose_context_schema(request, purpose):
    if purpose not in PURPOSE_CONTEXT_REGISTRY:
        raise NotFound(
            detail=(
                f"No context schema is registered for purpose "
                f"'{purpose}'."
            ),
            code="template_context_schema_not_found",
        )
    
    context_class = PURPOSE_CONTEXT_REGISTRY[purpose]
    schema = context_class.model_json_schema()
    flat = flatten_context_schema(schema)
    directives = annotate_directives(flat)

    if issubclass(context_class, PDFContext):
        directives = directives + [e.model_dump() for e in FORM_FIELD_ELEMENTS]

    return Response(directives, status=status.HTTP_200_OK)


