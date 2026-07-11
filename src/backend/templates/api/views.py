from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404

from consultation_backend.api_serializers import APIErrorResponseSerializer
from templates.models import Template, Purpose
from templates.api.serializers import TemplateSerializer
from templates.api import schemas
from templates.context_registry import PURPOSE_CONTEXT_REGISTRY, flatten_context_schema, annotate_directives
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
    templates = Template.objects.all()
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
    template = get_object_or_404(Template, purpose=purpose)
    return Response(TemplateSerializer(template).data, status=status.HTTP_200_OK)


@schemas.update_template
@api_view(["PUT"])
def update_template(request, purpose):
    if purpose not in Purpose.values:
        raise NotFound(
            detail=f"Unknown template purpose '{purpose}'.",
            code="unknown_template_purpose",
        )
    
    template, _ = Template.objects.get_or_create(purpose=purpose)
    serializer = TemplateSerializer(template, data=request.data, partial=True)
    
    serializer.is_valid(raise_exception=True)
    template = serializer.save()

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
    
    schema = PURPOSE_CONTEXT_REGISTRY[purpose].model_json_schema()
    flat = flatten_context_schema(schema)
    
    return Response(annotate_directives(flat), status=status.HTTP_200_OK)


