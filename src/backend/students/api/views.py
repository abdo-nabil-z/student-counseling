from rest_framework import status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, inline_serializer

from django.shortcuts import get_object_or_404

from students.models import Student
from students.api.serializers import StudentCreateSerializer, StudentDetailSerializer
from documents.api.serializers import DocumentInfoSerializer
from documents.services import attach_document

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
                400: OpenApiResponse(description="Validation errors"),
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

        if serializer.is_valid():
            student = serializer.save()

            response_serializer = StudentDetailSerializer(student)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@extend_schema_view(
    get=extend_schema(responses={200: StudentDetailSerializer}, description="Get one student", tags=["Students"]),
    patch=extend_schema(request=StudentCreateSerializer, responses={200: StudentDetailSerializer, 400: OpenApiResponse(description="Validation errors")}, description="Update a student", tags=["Students"]),
    delete=extend_schema(responses={204: OpenApiResponse(description="Deleted")}, description="Delete a student", tags=["Students"]),
)
@api_view(["GET", "PATCH", "DELETE"])
def detail_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "GET":
        return Response(StudentDetailSerializer(student).data)

    if request.method == "PATCH":
        serializer = StudentCreateSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(StudentDetailSerializer(student).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    student.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


_study_plan_upload_request = {"multipart/form-data": inline_serializer("StudyPlanUpload", fields={
    "file": drf_serializers.FileField(),
    "name": drf_serializers.CharField(required=False, help_text="Display name; defaults to filename"),
})}


@extend_schema(
    request=_study_plan_upload_request,
    responses={201: DocumentInfoSerializer, 400: OpenApiResponse(description="Validation errors"), 404: OpenApiResponse(description="Student not found")},
    description="Upload the initial study plan PDF for a student. Replaces any existing one.",
    tags=["Students"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_initial_study_plan(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    file = request.FILES.get("file")
    if not file:
        return Response({"file": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    if student.initial_study_plan:
        student.initial_study_plan.delete()
    doc = attach_document(file, request.data.get("name") or file.name)
    student.initial_study_plan = doc
    student.save(update_fields=["initial_study_plan"])
    return Response(DocumentInfoSerializer(doc, context={"request": request}).data, status=status.HTTP_201_CREATED)


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
    request=_study_plan_upload_request,
    responses={201: DocumentInfoSerializer, 400: OpenApiResponse(description="Validation errors"), 404: OpenApiResponse(description="Student not found")},
    description="Upload the final study plan PDF for a student. Replaces any existing one.",
    tags=["Students"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_final_study_plan(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    file = request.FILES.get("file")
    if not file:
        return Response({"file": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    if student.final_study_plan:
        student.final_study_plan.delete()
    doc = attach_document(file, request.data.get("name") or file.name)
    student.final_study_plan = doc
    student.save(update_fields=["final_study_plan"])
    return Response(DocumentInfoSerializer(doc, context={"request": request}).data, status=status.HTTP_201_CREATED)