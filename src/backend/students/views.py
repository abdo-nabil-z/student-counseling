from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

from students.models import Student
from students.api.serializers import (
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentDetailSerializer,
)


@extend_schema(
    methods=["GET"],
    responses={200: StudentDetailSerializer(many=True)},
    description="List all students",
    tags=["Students"],
)
@extend_schema(
    methods=["POST"],
    request=StudentCreateSerializer,
    responses={
        201: StudentDetailSerializer,
        400: OpenApiResponse(description="Validation errors"),
    },
    description="Create a new student",
    tags=["Students"],
)
@api_view(["GET", "POST"])
def create_list_students(request):
    if request.method == "GET":
        students = Student.objects.all().order_by("id")
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
    get=extend_schema(
        responses={200: StudentDetailSerializer},
        description="Get one student",
        tags=["Students"],
    ),
    patch=extend_schema(
        request=StudentUpdateSerializer,
        responses={
            200: StudentDetailSerializer,
            400: OpenApiResponse(description="Validation errors"),
        },
        description="Update a student",
        tags=["Students"],
    ),
    delete=extend_schema(
        responses={204: OpenApiResponse(description="Deleted")},
        description="Delete a student",
        tags=["Students"],
    ),
)
@api_view(["GET", "PATCH", "DELETE"])
def detail_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "GET":
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = StudentUpdateSerializer(
            student,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            student = serializer.save()
            response_serializer = StudentDetailSerializer(student)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)