from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from students.models import Student
from students.api.serializers import StudentCreateSerializer



@extend_schema(
        request=StudentCreateSerializer,
        responses={201: StudentCreateSerializer, 400: OpenApiResponse(description="Validation errors")},
        description="Create a new Student. Returns the created object on success.",
        examples=[OpenApiExample("Valid request",
                                value={"first_name": "Abdelrahman", "last_name": "Nabil", "user_id": "xy1234"},
                                request_only=True),],
        tags=["Students"],
)
@api_view(["POST"])
def create_student(request):
    serializer = StudentCreateSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
