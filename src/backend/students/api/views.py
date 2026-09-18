from rest_framework import status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, inline_serializer

from django.shortcuts import get_object_or_404

from consultation_backend.api_serializers import APIErrorResponseSerializer
from students.models import Student
from students.api.serializers import StudentCreateSerializer, StudentDetailSerializer, StudentUpdateSerializer
from students.services.semester_cleanup import delete_semester_data
from documents.api.serializers import DocumentInfoSerializer, DocumentUploadSerializer
from documents.services import replace_attached_document



@extend_schema_view(
        get=extend_schema(
            responses={200: StudentDetailSerializer(many=True)},
            description="List all students",
            tags=["Students"],
        ),
        post=extend_schema(
            request=StudentCreateSerializer,
            responses={
                201: StudentDetailSerializer,
                400: APIErrorResponseSerializer,
            },
            description="Create a new Student. Returns the created object on success.",
            examples=[OpenApiExample("Valid request",
                                value={"matriculation_number": "225202000","first_name": "Abdelrahman", "last_name": "Nabil", "email": "a.n@uni-rostock.de", "course_of_studies": "Informatik 2.0", "current_study_semester": 2, "credit_points": 36},
                                request_only=True,
                                ),
            ],
            tags=["Students"],
        )
)
@api_view(["GET", "POST"])
def create_list_students(request):
    if request.method == "GET":
        students = Student.objects.all()
        serializer = StudentDetailSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if request.method == "POST":
        serializer = StudentCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        response_serializer = StudentDetailSerializer(student)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



@extend_schema_view(
    get=extend_schema(
        responses={200: StudentDetailSerializer},
        description="Get one student",
        tags=["Students"]
    ),
    patch=extend_schema(
        request=StudentUpdateSerializer,
        responses={
            200: StudentDetailSerializer,
            400: APIErrorResponseSerializer,
        },
        description="Update a student",
        tags=["Students"]
    ),
    delete=extend_schema(
        responses={204: OpenApiResponse(description="Deleted")},
        description="Delete a student",
        tags=["Students"]
    ),
)
@api_view(["GET", "PATCH", "DELETE"])
def detail_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "GET":
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = StudentUpdateSerializer(student, data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        response_serializer = StudentDetailSerializer(student)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





@extend_schema(
    request=DocumentUploadSerializer,
    responses={
        201: DocumentInfoSerializer,
        400: OpenApiResponse(description="Validation errors"),
        404: OpenApiResponse(description="Student not found")
    },
    description="Upload the initial study plan file for a student. Replaces any existing one.",
    tags=["Students"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_initial_study_plan(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    serializer = DocumentUploadSerializer(data = request.data)
    
    serializer.is_valid(raise_exception=True)

    file = serializer.validated_data["file"]

    name = (serializer.validated_data.get("name") or file.name)

    document = replace_attached_document(
        instance=student,
        field_name="initial_study_plan",
        file=file,
        name=name,
    )

    response_serializer = DocumentInfoSerializer(
        document,
        context={
            "request": request,
        }
    )

    return Response(response_serializer.data, status=status.HTTP_201_CREATED)



@extend_schema(
    responses={404: OpenApiResponse(description="Student or appointment not found")},
    description="Get the appointment for a student. Returns 404 if the student has no appointment.",
    tags=["Students"],
)
@api_view(["GET"])
def get_student_appointment(request, student_id):
    from appointments.api.serializers import AppointmentDetailSerializer
    from appointments.models import Appointment
    student = get_object_or_404(Student, id=student_id)
    appointment = get_object_or_404(Appointment, student=student)
    return Response(AppointmentDetailSerializer(appointment).data)



@extend_schema(
    request=DocumentUploadSerializer,
    responses={
        201: DocumentInfoSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer
    },
    description="Upload the final study plan file for a student. Replaces any existing one.",
    tags=["Students"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_final_study_plan(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    serializer = DocumentUploadSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    file = serializer.validated_data["file"]

    name = (serializer.validated_data.get("name") or file.name)
    
    document = replace_attached_document(instance=student, field_name="final_study_plan", file=file, name=name)
    
    response_serializer = DocumentInfoSerializer(
        document,
        context={
            "request": request,
        },
    )

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
        request=inline_serializer(
            name="SemesterCleanupRequest",
            fields={
                "confirm": drf_serializers.CharField(),
            },
        ),
        responses={
            200:inline_serializer(
                name="SemesterCleanupResponse",
                fields={
                    "deleted_email_attachments": drf_serializers.IntegerField(),
                    "deleted_email_batches": drf_serializers.IntegerField(),
                    "deleted_email_deliveries": drf_serializers.IntegerField(),
                    "deleted_appointments": drf_serializers.IntegerField(),
                    "deleted_students": drf_serializers.IntegerField(),
                    "deleted_slots": drf_serializers.IntegerField(),
                },
            ),
            400: APIErrorResponseSerializer,
        },
        description=(
            "Delete all semester-specific data, including "
            "email history, appointments, students, "
            "student/appointment documents, and counselor "
            "availability slots. Persistent counselors and "
            "templates are preserved."
        ),
        tags=["Students"],
)
@api_view(["DELETE"])
def cleanup_semester_data(request):
    confirm = request.data.get("confirm")

    if confirm != "DELETE_SEMESTER_DATA":
        raise drf_serializers.ValidationError(
            {
                "confirm": [
                    (
                        "You must send "
                        "confirm='DELETE_SEMESTER_DATA' "
                        "to run semester cleanup."
                    )
                ]
            }
        )
    
    result = delete_semester_data()

    return Response(
        result,
        status=status.HTTP_200_OK,
    )