from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from consultation_backend.api_serializers import APIErrorResponseSerializer
from mailing.api.serializers import EmailBatchCreateSerializer, EmailBatchDetailSerializer
from mailing.services.generation import generate_email_batch



@extend_schema(
    request=EmailBatchCreateSerializer,
    responses={
        201: EmailBatchDetailSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        422: APIErrorResponseSerializer,
    },
    description=(
        "Generate a personalized email batch for the selected students."
        " Preview mode creates draft deliveries; "
        "automatic mode creates queued deliveries."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def create_email_batch(request):
    serializer = EmailBatchCreateSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    batch = generate_email_batch(
        purpose=(serializer.validated_data["purpose"]),
        student_ids=(serializer.validated_data["student_ids"]),
        send_immediately=(serializer.validated_data["send_immediately"])
    )

    response_serializer = (EmailBatchDetailSerializer(batch))

    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
