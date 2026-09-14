from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from consultation_backend.api_serializers import APIErrorResponseSerializer
from mailing.api.serializers import (
    EmailBatchCreateSerializer,
    EmailBatchDetailSerializer,
    EmailDeliveryPreviewSerializer,
    EmailDeliveryUpdateSerializer,
    EmailBatchStatusSerializer,
)
from mailing.api_exceptions import EmailDeliveryNotEditable
from mailing.models import EmailBatch, EmailDelivery
from mailing.services.generation import generate_email_batch
from mailing.services.queueing import queue_email_batch
from mailing.services.resending import requeue_failed_delivery
from mailing.services.status import build_email_batch_status



@extend_schema(
    request=EmailBatchCreateSerializer,
    responses={
        201: EmailBatchDetailSerializer,
        400: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
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


@extend_schema(
        responses={
            200: EmailBatchDetailSerializer,
            404: APIErrorResponseSerializer,
        },
        description=("Get an email batch and all generated emmail deliveries for preview."),
        tags=["Mailing"],
    
)
@api_view(["GET"])
def get_email_batch(request, batch_id):
    batch = get_object_or_404(EmailBatch.objects.prefetch_related("deliveries__student"),pk=batch_id)

    serializer = EmailBatchDetailSerializer(batch)

    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    methods=["GET"],
    responses={
        200: EmailDeliveryPreviewSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Get one generated email delivery."
    ),
    tags=["Mailing"],
)
@extend_schema(
    methods=["PATCH"],
    request=EmailDeliveryUpdateSerializer,
    responses={
        200: EmailDeliveryPreviewSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Edit the subject or body of a draft "
        "email before it is queued for sending."
    ),
    tags=["Mailing"],
)
@api_view(["GET", "PATCH"])
def email_delivery_detail(request, delivery_id):
    delivery = get_object_or_404(EmailDelivery.objects.select_related("student", "batch"), pk=delivery_id)

    if request.method == "GET":
        serializer = (EmailDeliveryPreviewSerializer(delivery))

        return Response(serializer.data, status=status.HTTP_200_OK)

    editable_statuses = {
        EmailDelivery.Status.DRAFT,
        EmailDelivery.Status.FAILED,
    }

    if delivery.status not in editable_statuses:
        raise EmailDeliveryNotEditable(
            details={
                "delivery_id": delivery.pk,
                "status": delivery.status,
            }
        )

    serializer = EmailDeliveryUpdateSerializer(delivery, data=request.data, partial=True)

    serializer.is_valid(raise_exception=True)

    delivery = serializer.save()

    response_serializer = EmailDeliveryPreviewSerializer(delivery)

    return Response(response_serializer.data, status=status.HTTP_200_OK)



@extend_schema(
    request=None,
    responses={
        202: EmailBatchDetailSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Queue all draft emails in a reviewed "
        "batch for sending."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def send_email_batch(request, batch_id):
    batch = get_object_or_404(EmailBatch, pk=batch_id)

    queue_email_batch(batch)

    batch = EmailBatch.objects.prefetch_related("deliveries__student").get(pk=batch.pk)

    serializer = EmailBatchDetailSerializer(batch)

    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    responses={
        200: EmailBatchStatusSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Get the current sending status of an "
        "email batch for frontend polling."
    ),
    tags=["Mailing"],
)
@api_view(["GET"])
def get_email_batch_status(request, batch_id):
    batch = get_object_or_404(EmailBatch, pk=batch_id)

    batch_status = build_email_batch_status(batch)

    serializer = EmailBatchStatusSerializer(batch_status)

    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=None,
    responses={
        202: EmailDeliveryPreviewSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Queue a failed email delivery for "
        "another sending cycle."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def resend_email_delivery(request, delivery_id):
    delivery = get_object_or_404(
        EmailDelivery.objects.select_related("student", "batch"), pk= delivery_id
    )

    delivery = requeue_failed_delivery(delivery)

    serializer = EmailDeliveryPreviewSerializer(delivery)

    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)