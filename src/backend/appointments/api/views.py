# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, parser_classes
# from rest_framework.parsers import MultiPartParser
# from drf_spectacular.utils import extend_schema, OpenApiParameter
# from drf_spectacular.types import OpenApiTypes
# from django.shortcuts import get_object_or_404


# from consultation_backend.api_serializers import APIErrorResponseSerializer
# from appointments.models import Appointment
# from appointments.api.serializers import AppointmentSerializer, AppointmentDetailSerializer, AppointmentUpdateSerializer, AppointmentFilterSerializer
# from documents.api.serializers import DocumentInfoSerializer, DocumentUploadSerializer
# from documents.services import replace_attached_document


# @extend_schema(
#         request=AppointmentSerializer,
#         responses={
#             201: AppointmentSerializer,
#             400: APIErrorResponseSerializer,
#         },
#         description="Create a new Appointment linking the student and the counselor and the time slot",
#         tags=["Appointments"],
# )
# @api_view(["POST"])
# def create_appointment(request):
#     serializer = AppointmentSerializer(data = request.data)

#     serializer.is_valid(raise_exception=True)
#     appointment = serializer.save()

#     response_serializer = AppointmentSerializer(appointment)

#     return Response(response_serializer.data, status=status.HTTP_201_CREATED)



# @extend_schema(
#         parameters=[
#             OpenApiParameter("student", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filter by student ID"),
#             OpenApiParameter("counselor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filter by counselor ID"),
#         ],
#         responses={
#             200: AppointmentDetailSerializer(many=True),
#             400: APIErrorResponseSerializer,
#         },
#         description="List all appointments, optionally filtered by student and/or counselor",
#         tags=["Appointments"],
# )
# @api_view(["GET"])
# def list_appointments(request):
#     appointments = Appointment.objects.all()

#     filter_serializer = AppointmentFilterSerializer(data=request.query_params)
#     filter_serializer.is_valid(raise_exception=True)

#     student_id = filter_serializer.validated_data.get("student")
#     counselor_id = filter_serializer.validated_data.get("counselor")

#     if student_id is not None:
#         appointments = appointments.filter(student_id=student_id)
#     if counselor_id is not None:
#         appointments = appointments.filter(counselor_id=counselor_id)
    
#     return Response(AppointmentDetailSerializer(appointments, many=True).data)


# @extend_schema(
#         responses={
#             200: AppointmentDetailSerializer,
#             404: APIErrorResponseSerializer,
#         },
#         description="Retrieve a specific appointment by ID.",
#         tags=["Appointments"],
#         methods=["GET"],
# )
# @extend_schema(
#     request=AppointmentUpdateSerializer,
#     responses={
#         200: AppointmentDetailSerializer,
#         400: APIErrorResponseSerializer,
#         404: APIErrorResponseSerializer,
#     },
#     description="Update an appointment. Use this for rescheduling or updating the appointment information",
#     tags=["Appointments"],
#     methods=["PATCH"],
# )
# @api_view(["GET", "PATCH"])
# def detail_update_appointment(request, appointment_id):
#     appointment =get_object_or_404(Appointment, id=appointment_id)

#     if request.method == "GET":
#         serializer = AppointmentDetailSerializer(appointment)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     if request.method == "PATCH":
#         serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)

#         serializer.is_valid(raise_exception=True)
#         appointment = serializer.save()

#         response_serializer = AppointmentDetailSerializer(appointment)

#         return Response(response_serializer.data, status=status.HTTP_200_OK)


# @extend_schema(
#     request=DocumentUploadSerializer,
#     responses={
#         201: DocumentInfoSerializer,
#         400: APIErrorResponseSerializer,
#         404: APIErrorResponseSerializer,
#     },
#     description="Upload the minutes file for an appointment. Replaces any existing one.",
#     tags=["Appointments"],
# )
# @api_view(["POST"])
# @parser_classes([MultiPartParser])
# def upload_appointment_minutes(request, appointment_id):
#     appointment = get_object_or_404(Appointment, id=appointment_id)
    
#     serializer = DocumentUploadSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)

#     file = serializer.validated_data["file"]

#     name = (serializer.validated_data.get("name") or file.name)

#     document = replace_attached_document(
#         instance=appointment,
#         field_name="minutes",
#         file=file,
#         name=name,
#     )
    
#     response_serializer = DocumentInfoSerializer(
#         document,
#         context={
#             "request": request,
#         },
#     )

#     return Response(response_serializer.data, status=status.HTTP_201_CREATED)


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404


from consultation_backend.api_serializers import APIErrorResponseSerializer
from appointments.models import Appointment
from appointments.api.serializers import AppointmentSerializer, AppointmentDetailSerializer, AppointmentUpdateSerializer, AppointmentFilterSerializer
from documents.api.serializers import DocumentInfoSerializer, DocumentUploadSerializer
from documents.services import replace_attached_document


@extend_schema(
    request=AppointmentSerializer,
    responses={
        201: AppointmentSerializer,
        400: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Create a new appointment for a student and counselor. "
        "The availability slot is optional. If a slot is provided, "
        "it must belong to the selected counselor and the appointment "
        "must fit inside it. Active appointments (pending or booked) "
        "that overlap another active appointment for the same counselor "
        "return an appointment_overlap_warning unless allow_overlap=true."
    ),
    tags=["Appointments"],
)
@api_view(["POST"])
def create_appointment(request):
    serializer = AppointmentSerializer(data = request.data)

    serializer.is_valid(raise_exception=True)
    appointment = serializer.save()

    response_serializer = AppointmentSerializer(appointment)

    return Response(response_serializer.data, status=status.HTTP_201_CREATED)



@extend_schema(
        parameters=[
            OpenApiParameter("student", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filter by student ID"),
            OpenApiParameter("counselor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filter by counselor ID"),
        ],
        responses={
            200: AppointmentDetailSerializer(many=True),
            400: APIErrorResponseSerializer,
        },
        description="List all appointments, optionally filtered by student and/or counselor",
        tags=["Appointments"],
)
@api_view(["GET"])
def list_appointments(request):
    appointments = Appointment.objects.all()

    filter_serializer = AppointmentFilterSerializer(data=request.query_params)
    filter_serializer.is_valid(raise_exception=True)

    student_id = filter_serializer.validated_data.get("student")
    counselor_id = filter_serializer.validated_data.get("counselor")

    if student_id is not None:
        appointments = appointments.filter(student_id=student_id)
    if counselor_id is not None:
        appointments = appointments.filter(counselor_id=counselor_id)

    return Response(AppointmentDetailSerializer(appointments, many=True).data)



@extend_schema(
        responses={
            200: AppointmentDetailSerializer,
            404: APIErrorResponseSerializer,
        },
        description="Retrieve a specific appointment by ID.",
        tags=["Appointments"],
        methods=["GET"],
)
@extend_schema(
    request=AppointmentUpdateSerializer,
    responses={
        200: AppointmentDetailSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Update or reschedule an appointment. If a slot is provided, "
        "it must belong to the selected counselor and the appointment "
        "must fit inside it. Rescheduling an active appointment so that "
        "it overlaps another active appointment for the same counselor "
        "returns an appointment_overlap_warning unless allow_overlap=true. "
        "Cancelled, missed, and completed appointments do not block availability."
    ),
    tags=["Appointments"],
    methods=["PATCH"],
)
@extend_schema(
    responses={
        204: OpenApiResponse(description="Deleted"),
        404: APIErrorResponseSerializer,
    },
    description="Delete an appointment. The student becomes bookable again.",
    tags=["Appointments"],
    methods=["DELETE"],
)
@api_view(["GET", "PATCH", "DELETE"])
def detail_update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "GET":
        serializer = AppointmentDetailSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        response_serializer = AppointmentDetailSerializer(appointment)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        appointment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary", "description": "File to upload. Any file type is accepted."},
                "name": {"type": "string", "description": "Display name; defaults to filename"},
            },
            "required": ["file"],
        }
    },
    responses={
        201: DocumentInfoSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer
    },
    description="Upload the minutes file for an appointment. Replaces any existing one.",
    tags=["Appointments"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_appointment_minutes(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    serializer = DocumentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    file = serializer.validated_data["file"]

    name = (serializer.validated_data.get("name") or file.name)

    document = replace_attached_document(
        instance=appointment,
        field_name="minutes",
        file=file,
        name=name,
    )

    response_serializer = DocumentInfoSerializer(
        document,
        context={
            "request": request,
        },
    )

    return Response(response_serializer.data, status=status.HTTP_201_CREATED)