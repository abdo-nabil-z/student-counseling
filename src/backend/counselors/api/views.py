from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from counselors.models import Counselor, AvailabilityBlock
from counselors.api.serializers import CounselorCreateSerializer, CounselorDetailSerializer, AvailabilityBlockCreateSerializer, AvailabilityBlockDetailSerializer


@extend_schema_view(
        get=extend_schema(
            responses={200: CounselorDetailSerializer(many=True)},
            description="List all counselors",
            tags=["Counselors"],
        ),
        post=extend_schema(
            request=CounselorCreateSerializer,
            responses={
                201: CounselorDetailSerializer,
                400: OpenApiResponse(description="Validation errors"),
            },
            description="Create a new Counselor. Returns the created object on success.",
            examples=[OpenApiExample("Valid request",
                                value={"title": "Prof.", "first_name": "Abdelrahman", "last_name": "Nabil", "chair": "AVA", "office_address": "AE22-R242", "email": "a.n@uni-rostock.de", "additional_cc": ["1.2@uni-rostock.de", "3.4@uni-rostock.de"]},
                                request_only=True,
                                ),
            ],
            tags=["Counselors"],
        )
)
@api_view(["GET","POST"])
def create_list_counselors(request):
    if request.method == "GET":
        counselors = Counselor.objects.all()
        serializer = CounselorDetailSerializer(counselors, many=True)
        return Response(serializer.data, status= status.HTTP_200_OK)
        
    if request.method == "POST":
        serializer = CounselorCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                name="counselor_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the counselor"
            )
        ],
        responses={200: AvailabilityBlockDetailSerializer(many=True)},
        description="Get all availability blocks for a specific counselor",
        tags=["Counselors"],
    ),
    post=extend_schema(
        parameters=[
            OpenApiParameter(
                name="counselor_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the counselor.",
            ),
        ],
        request=AvailabilityBlockCreateSerializer,
        responses={
            201: AvailabilityBlockDetailSerializer,
            400: OpenApiResponse(description="Validation errors"),
            404: OpenApiResponse(description="Counselor not found"),
        },
        description="Create an availability block for a specific counselor.",
        tags=["Counselors"],
    ),
)
@api_view(["GET","POST"])
def create_list_counselor_time_slot(request, counselor_id):
    counselor = get_object_or_404(Counselor, id=counselor_id)
    
    if request.method == "GET":
        counselor_time_slots = AvailabilityBlock.objects.filter(counselor=counselor)

        serializer = AvailabilityBlockDetailSerializer(counselor_time_slots, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if request.method == "POST":
        serializer = AvailabilityBlockCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(counselor=counselor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)