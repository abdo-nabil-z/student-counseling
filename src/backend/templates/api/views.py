from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from templates.models import Template, Purpose, TemplatePurpose
from templates.api.serializers import TemplateSerializer, TemplateRenderTestmailRequestSerializer
from templates.api import schemas
from templates.context_registry import PURPOSE_CONTEXT_REGISTRY, TestmailContext, flatten_context_schema
from django.shortcuts import get_object_or_404

    



@schemas.templates_by_purpose
@api_view(["GET"])
def templates_by_purpose(request):
    purpose_key = request.query_params.get("purpose")
    if purpose_key:
        if purpose_key not in Purpose.values:
            return Response({"error": "Invalid purpose"}, status=status.HTTP_400_BAD_REQUEST)
        templates = Template.objects.filter(template_purposes__purpose=purpose_key)
    else:
        templates = Template.objects.all()
    serializer = TemplateSerializer(templates, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@schemas.create_template
@api_view(["PUT"])
def create_template(request):
    serializer = TemplateSerializer(data=request.data)
    if serializer.is_valid():
        template = serializer.save()
        return Response(TemplateSerializer(template).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@schemas.update_template
@api_view(["PUT"])
def update_template(request, template_id):
    template = get_object_or_404(Template, id=template_id)

    serializer = TemplateSerializer(template, data=request.data, partial=True)
    if serializer.is_valid():
        template = serializer.save()
        return Response(TemplateSerializer(template).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@schemas.delete_template
@api_view(["DELETE"])
def delete_template(request, template_id):
    template = get_object_or_404(Template, id=template_id)
    template.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@schemas.purposes_list
@api_view(["GET"])
def purposes_list(request):
    result = []
    for value, label in Purpose.choices:
        default_tp = TemplatePurpose.objects.filter(purpose=value, default=True).first()
        result.append({
            "key": value,
            "label": label,
            "default_template_id": default_tp.template_id if default_tp else None,
        })
    return Response(result, status=status.HTTP_200_OK)


@schemas.purpose_context_schema
@api_view(["GET"])
def purpose_context_schema(request, purpose):
    if purpose not in PURPOSE_CONTEXT_REGISTRY:
        return Response(
            {"error": f"No context schema registered for purpose '{purpose}'"},
            status=status.HTTP_404_NOT_FOUND,
        )
    schema = PURPOSE_CONTEXT_REGISTRY[purpose].model_json_schema()
    return Response(flatten_context_schema(schema), status=status.HTTP_200_OK)


@schemas.set_default_template
@api_view(["PUT"])
def set_default_template(request, purpose):
    if purpose not in Purpose.values:
        return Response({"error": "Invalid purpose"}, status=status.HTTP_400_BAD_REQUEST)
    template_id = request.data.get("template_id")
    if not template_id:
        return Response({"error": "template_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not TemplatePurpose.objects.filter(purpose=purpose, template_id=template_id).exists():
        return Response({"error": "Template is not linked to this purpose"}, status=status.HTTP_400_BAD_REQUEST)
    TemplatePurpose.objects.filter(purpose=purpose, default=True).update(default=False)
    TemplatePurpose.objects.filter(purpose=purpose, template_id=template_id).update(default=True)
    return Response(status=status.HTTP_204_NO_CONTENT)

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def render_template_for_testmail(request):
    return Response({
        "subject": "Test mail",
        "body": "This is a temporary test mail preview."
    })