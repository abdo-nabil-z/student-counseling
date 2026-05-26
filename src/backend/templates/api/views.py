from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers

from counselors.models import AvailabilitySlot, Counselor
from templates.models import Template, Purpose, TemplatePurpose
from templates.api.serializers import TemplateSerializer, TemplateRenderTestmailRequestSerializer

from jinja2.sandbox import SandboxedEnvironment


def generate_from_template(template_str, **context):
    env = SandboxedEnvironment()
    return env.from_string(template_str).render(**context)




@extend_schema(
    parameters=[
        OpenApiParameter(name="template_id", type=int, location=OpenApiParameter.QUERY, required=True, description="ID of the template to render"),
    ],
    request=TemplateRenderTestmailRequestSerializer,
    responses={
        200: inline_serializer(
            name="TestmailRenderResponse",
            fields={"rendered": serializers.CharField()}
        ),
        400: inline_serializer(name="TestmailError400", fields={"error": serializers.CharField()}),
        404: inline_serializer(name="TestmailError404", fields={"error": serializers.CharField()}),
    },
    description="Render a testmail template for a counselor, injecting their available slots into the context",
)
@api_view(["POST"])
def generate_template_for_testmail(request):
    template_id = request.query_params.get("template_id")
    if not template_id:
        return Response({"error": "Template ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TemplateRenderTestmailRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    counselor_id = serializer.validated_data["counselor"]
    counselor = Counselor.objects.filter(id=counselor_id).first()
    if not counselor:
        return Response({"error": "Counselor not found"}, status=status.HTTP_404_NOT_FOUND)
    slots = list(counselor.availability_slots.filter(status=AvailabilitySlot.Status.AVAILABLE).order_by("start_time"))
    
    rendered = generate_from_template(template.content, counselor=counselor, slots=slots)
    return Response({"rendered": rendered}, status=status.HTTP_200_OK)
    
    
    
    
    

@extend_schema(
        parameters=[
            OpenApiParameter(name="purpose", type=str, location=OpenApiParameter.QUERY, required=False, description="Filter templates by purpose key"),
        ],
        request=None,
        responses={
            200: TemplateSerializer(many=True),
            400: inline_serializer(name="ErrorResponse", fields={"error": serializers.CharField()}),
        },
        description="Get templates, optionally filtered by purpose key",
)
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


@extend_schema(
    request=TemplateSerializer,
    responses={
        201: TemplateSerializer,
        400: inline_serializer(name="CreateTemplateError400", fields={"error": serializers.CharField()}),
    },
    description="Create a new template",
)
@api_view(["PUT"])
def create_template(request):
    serializer = TemplateSerializer(data=request.data)
    if serializer.is_valid():
        template = serializer.save()
        return Response(TemplateSerializer(template).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=TemplateSerializer,
    responses={
        200: TemplateSerializer,
        400: inline_serializer(name="UpdateTemplateError400", fields={"error": serializers.CharField()}),
        404: inline_serializer(name="UpdateTemplateError404", fields={"error": serializers.CharField()}),
    },
    description="Partially update an existing template",
)
@api_view(["PUT"])
def update_template(request, template_id):
    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = TemplateSerializer(template, data=request.data, partial=True)
    if serializer.is_valid():
        template = serializer.save()
        return Response(TemplateSerializer(template).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=None,
    responses={
        204: None,
        404: inline_serializer(name="DeleteTemplateError404", fields={"error": serializers.CharField()}),
    },
    description="Delete a template by ID",
)
@api_view(["DELETE"])
def delete_template(request, template_id):
    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)

    template.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
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


@extend_schema(
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

