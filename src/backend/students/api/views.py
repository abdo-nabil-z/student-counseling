from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from students.models import Student
from students.api.serializers import StudentCreateSerializer, StudentDetailSerializer



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
