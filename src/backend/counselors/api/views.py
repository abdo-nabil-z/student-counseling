from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse

from counselors.models import Counselor
from counselors.api.serializers import CounselorCreateSerializer, AvailabilitySlotSerializer


@extend_schema(
        request=CounselorCreateSerializer,
        responses={201: CounselorCreateSerializer, 400: dict},
        description="Create a new counselor"
)
@api_view(["POST"])
def create_counselor(request):
    serializer = CounselorCreateSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
        request=AvailabilitySlotSerializer,
        responses={201: AvailabilitySlotSerializer, 400: OpenApiResponse(description="Validation errors")},
        description="Create a new time slot for the counselor"
)
@api_view(["POST"])
def create_counselor_time_slot(request):
    serializer = AvailabilitySlotSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)