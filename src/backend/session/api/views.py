from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from session.models import CounselingSession
from session.api.serializers import CounselingSessionSerializer


@extend_schema(
        request=CounselingSessionSerializer,
        responses={201: CounselingSessionSerializer, 400: OpenApiResponse(description="Validation errors")},
        description="Create a new Session linking the student and the counselor and the time slot",
        tags=["Sessions"],
)
@api_view(["POST"])
def create_session(request):
    serializer = CounselingSessionSerializer(data = request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)