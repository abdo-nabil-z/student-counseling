from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from consultation_backend.api_serializers import APIErrorResponseSerializer
from counselors.models import Counselor, Slot
from counselors.api.serializers import (
    CounselorCreateSerializer,
    CounselorUpdateSerializer,
    CounselorDetailSerializer,
    SlotCreateSerializer,
    SlotDetailSerializer,
    CounselorSlotStatusSerializer,
)
from counselors.services.slot_status import build_counselor_slot_status, build_all_counselor_slot_statuses


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
            400: APIErrorResponseSerializer,
        },
        description="Create a new counselor",
        tags=["Counselors"],
    ),
)
@api_view(["GET", "POST"])
def create_list_counselors(request):
    if request.method == "GET":
        counselors = Counselor.objects.all().order_by("id")
        serializer = CounselorDetailSerializer(counselors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = CounselorCreateSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    counselor = serializer.save()

    response_serializer = CounselorDetailSerializer(counselor)

    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        responses={200: CounselorDetailSerializer},
        description="Get one counselor",
        tags=["Counselors"],
    ),
    patch=extend_schema(
        request=CounselorUpdateSerializer,
        responses={
            200: CounselorDetailSerializer,
            400: APIErrorResponseSerializer,
        },
        description="Update a counselor",
        tags=["Counselors"],
    ),
    delete=extend_schema(
        responses={204: OpenApiResponse(description="Deleted")},
        description="Delete a counselor",
        tags=["Counselors"],
    ),
)
@api_view(["GET", "PATCH", "DELETE"])
def detail_counselor(request, counselor_id):
    counselor = get_object_or_404(Counselor, id=counselor_id)

    if request.method == "GET":
        serializer = CounselorDetailSerializer(counselor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = CounselorUpdateSerializer(
            counselor,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        counselor = serializer.save()

        response_serializer = CounselorDetailSerializer(counselor)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        counselor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    methods=["GET"],
    responses={200: SlotDetailSerializer(many=True)},
    description="List slots for one counselor",
    tags=["Counselors"],
)
@extend_schema(
    methods=["POST"],
    request=SlotCreateSerializer,
    responses={
        201: SlotDetailSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Create an availability slot for one counselor. "
        "Availability slots may overlap; appointment conflicts "
        "are validated separately."
    ),
    tags=["Counselors"],
)
@api_view(["GET", "POST"])
def create_list_counselor_slots(request, counselor_id):
    counselor = get_object_or_404(Counselor, id=counselor_id)

    if request.method == "GET":
        slots = Slot.objects.filter(counselor=counselor).order_by(
            "date",
            "start_time",
        )
        serializer = SlotDetailSerializer(slots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        
        serializer = SlotCreateSerializer(data=request.data, context={"counselor": counselor})

        serializer.is_valid(raise_exception=True)
        slot = serializer.save(counselor=counselor)

        response_serializer = SlotDetailSerializer(slot)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



@extend_schema(
    responses={
        200: CounselorSlotStatusSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Return one counselor's availability slots split into free "
        "and taken time segments. Only pending and booked appointments "
        "occupy availability. Cancelled, missed, and completed "
        "appointments are ignored. Active appointments outside all "
        "availability slots are returned as uncovered_appointments."
    ),
    tags=["Counselors"],
)
@api_view(["GET"])
def get_counselor_slot_status(request, counselor_id):
    counselor = get_object_or_404(Counselor, id=counselor_id)

    return Response(
        build_counselor_slot_status(counselor),
        status=status.HTTP_200_OK,
    )


@extend_schema(
    responses={
        200: CounselorSlotStatusSerializer(many=True),
    },
    description=(
        "Return availability for all counselors, split into free "
        "and taken segments. Appointment occupation is calculated "
        "independently for each counselor; appointments belonging "
        "to different counselors do not conflict."
    ),
    tags=["Counselors"],
)
@api_view(["GET"])
def list_all_counselor_slot_statuses(request):
    return Response(
        build_all_counselor_slot_statuses(),
        status=status.HTTP_200_OK,
    )
