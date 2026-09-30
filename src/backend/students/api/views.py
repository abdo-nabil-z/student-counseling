import pandas as pd

from rest_framework import status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, inline_serializer

from django.shortcuts import get_object_or_404

from consultation_backend.api_serializers import APIErrorResponseSerializer
from students.models import Student
from students.api.serializers import StudentCreateSerializer, StudentDetailSerializer, StudentUpdateSerializer
from students.services.semester_cleanup import delete_semester_data
from documents.api.serializers import DocumentInfoSerializer, DocumentUploadSerializer
from documents.services import replace_attached_document
from appointments.api.serializers import AppointmentDetailSerializer

from .import_utils import (
    parse_file,
    EXPECTED_COLUMNS,
)


class StudentImportPreviewView(APIView):
    """
    POST /api/students/import/preview/

    Accepts an uploaded file (multipart/form-data, field name "file"),
    parses it, and returns a row-by-row validation preview. Nothing is
    created here — this is read-only.
    """

    parser_classes = [MultiPartParser]

    @extend_schema(
        request=inline_serializer(
            name="StudentImportPreviewRequest",
            fields={"file": drf_serializers.FileField()},
        ),
        responses={
            200: inline_serializer(
                name="StudentImportPreviewResponse",
                fields={
                    "total": drf_serializers.IntegerField(),
                    "valid": drf_serializers.IntegerField(),
                    "invalid": drf_serializers.IntegerField(),
                    "students": drf_serializers.ListField(
                        child=drf_serializers.DictField()
                    ),
                },
            ),
            400: APIErrorResponseSerializer,
        },
        description=(
            "Parse an uploaded Excel/CSV file and return a row-by-row "
            "preview with validation errors, without creating anything."
        ),
        tags=["Students"],
    )
    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            raise drf_serializers.ValidationError(
                {"file": ["No file uploaded."]}
            )

        try:
            df = parse_file(uploaded_file)
        except Exception as exc:
            raise drf_serializers.ValidationError(
                {"file": [f"Could not read file: {exc}"]}
            )

        existing_matriculation_numbers = set(
            Student.objects.values_list("matriculation_number", flat=True)
        )
        existing_emails = set(
            Student.objects.values_list("email", flat=True)
        )

        # Track matriculation numbers / emails seen *within this file* so
        # duplicate rows in the same upload are flagged here too, not just
        # against the database.
        seen_matriculation_numbers = set()
        seen_emails = set()

        students = []

        for index, row in df.iterrows():
            student = {}

            for column in EXPECTED_COLUMNS:
                value = row.get(column, "")

                # pandas represents a blank Excel cell as NaN (a float),
                # not None — `value is None` alone misses it and the cell
                # ends up as the literal string "nan".
                if value is None or pd.isna(value):
                    value = ""

                student[column] = str(value).strip()

            matriculation = student["matriculation_number"]
            email = student["email"]

            errors = []

            if not matriculation:
                errors.append("Missing matriculation number")
            if not student["first_name"]:
                errors.append("Missing first name")
            if not student["last_name"]:
                errors.append("Missing last name")
            if not email:
                errors.append("Missing email")

            if matriculation:
                if matriculation in existing_matriculation_numbers:
                    errors.append("Student already exists")
                elif matriculation in seen_matriculation_numbers:
                    errors.append("Duplicate matriculation number in this file")

            if email:
                if email in existing_emails:
                    errors.append("Email already exists")
                elif email in seen_emails:
                    errors.append("Duplicate email in this file")

            if matriculation:
                seen_matriculation_numbers.add(matriculation)
            if email:
                seen_emails.add(email)

            student["_row"] = index + 2  # +2: 1-based, plus the header row
            student["_errors"] = errors
            student["_valid"] = len(errors) == 0

            students.append(student)

        return Response(
            {
                "total": len(students),
                "valid": sum(1 for s in students if s["_valid"]),
                "invalid": sum(1 for s in students if not s["_valid"]),
                "students": students,
            }
        )


class StudentImportConfirmView(APIView):
    """
    POST /api/students/import/confirm/

    Accepts the list of rows the user chose to keep after reviewing the
    preview, and actually creates them. Reuses StudentCreateSerializer so
    the model's own validation (e.g. the digits-only matriculation-number
    regex) is enforced, instead of calling Student.objects.create()
    directly and bypassing it.
    """

    @extend_schema(
        request=inline_serializer(
            name="StudentImportConfirmRequest",
            fields={"students": StudentCreateSerializer(many=True)},
        ),
        responses={
            201: inline_serializer(
                name="StudentImportConfirmResponse",
                fields={
                    "created": drf_serializers.IntegerField(),
                    "errors": drf_serializers.ListField(
                        child=drf_serializers.DictField()
                    ),
                },
            ),
            400: APIErrorResponseSerializer,
        },
        description=(
            "Create students from previously previewed import rows. Rows "
            "that fail validation are skipped and reported individually — "
            "earlier valid rows in the same request are still created."
        ),
        tags=["Students"],
    )
    def post(self, request):
        rows = request.data.get("students", [])

        if not rows:
            raise drf_serializers.ValidationError(
                {"students": ["No students provided."]}
            )

        # email has no unique=True on the model, so uniqueness isn't
        # enforced by StudentCreateSerializer — kept as an explicit
        # business-rule check here, same as the preview view.
        existing_emails = set(
            Student.objects.values_list("email", flat=True)
        )
        seen_emails = set()

        created_ids = []
        errors = []

        for index, data in enumerate(rows):
            row_number = index + 2  # matches the preview view's numbering

            email = str(data.get("email", "")).strip()

            if email and (email in existing_emails or email in seen_emails):
                errors.append(
                    {"row": row_number, "errors": {"email": ["Email already exists"]}}
                )
                continue

            serializer = StudentCreateSerializer(data=data)

            if serializer.is_valid():
                student = serializer.save()
                created_ids.append(student.id)
                if email:
                    seen_emails.add(email)
            else:
                errors.append({"row": row_number, "errors": serializer.errors})

        return Response(
            {
                "created": len(created_ids),
                "errors": errors,
            },
            status=status.HTTP_201_CREATED,
        )


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
        description=(
            "Update a student. contact_status may be edited manually "
            "and can also be updated automatically by mailing and "
            "appointment workflows."
        ),
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
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
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
    responses={
        200: AppointmentDetailSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Get the appointment associated with a student. "
        "Returns 404 if the student does not exist or has no appointment."
    ),
    tags=["Students"],
)
@api_view(["GET"])
def get_student_appointment(request, student_id):
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