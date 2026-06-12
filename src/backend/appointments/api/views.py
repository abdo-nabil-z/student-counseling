from rest_framework import status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer

from django.shortcuts import get_object_or_404

from appointments.models import Appointment
from appointments.api.serializers import AppointmentSerializer
from documents.api.serializers import DocumentInfoSerializer
from documents.services import attach_document


@extend_schema(
        request=AppointmentSerializer,
        responses={201: AppointmentSerializer, 400: OpenApiResponse(description="Validation errors")},
        description="Create a new Appointment linking the student and the counselor and the time slot",
        tags=["Appointments"],
)
@api_view(["POST"])
def create_appointment(request):
    serializer = AppointmentSerializer(data = request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from appointments.api.serializers import AppointmentDetailSerializer

@extend_schema(
        responses={200: AppointmentDetailSerializer(many=True)},
        description="List all appointments",
        tags=["Appointments"],
)
@api_view(["GET"])
def list_appointments(request):
    appointments = Appointment.objects.all()
    return Response(AppointmentDetailSerializer(appointments, many=True).data)


@extend_schema(
    request={"multipart/form-data": inline_serializer("AppointmentMinutesUpload", fields={
        "file": drf_serializers.FileField(),
        "name": drf_serializers.CharField(required=False, help_text="Display name; defaults to filename"),
    })},
    responses={201: DocumentInfoSerializer, 400: OpenApiResponse(description="Validation errors"), 404: OpenApiResponse(description="Appointment not found")},
    description="Upload the minutes PDF for an appointment. Replaces any existing one.",
    tags=["Appointments"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_appointment_minutes(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    file = request.FILES.get("file")
    if not file:
        return Response({"file": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    if appointment.minutes:
        appointment.minutes.delete()
    doc = attach_document(file, request.data.get("name") or file.name)
    appointment.minutes = doc
    appointment.save(update_fields=["minutes"])
    return Response(DocumentInfoSerializer(doc, context={"request": request}).data, status=status.HTTP_201_CREATED)