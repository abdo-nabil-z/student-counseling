import logging
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from consultation_backend.api_serializers import APIErrorResponseSerializer
from consultation_backend.api_exceptions import FileStorageUnavailable, StoredFileNotFound
from mailing.api.serializers import (
    EmailBatchCreateSerializer,
    EmailBatchDetailSerializer,
    EmailDeliveryPreviewSerializer,
    EmailDeliveryUpdateSerializer,
    EmailBatchStatusSerializer,
    EmailAttachmentSerializer,
    EmailAttachmentUploadSerializer,
    ExistingEmailAttachmentSerializer,
)
from mailing.api_exceptions import EmailDeliveryNotEditable
from mailing.models import EmailBatch, EmailDelivery, EmailAttachment
from mailing.services.generation import generate_email_batch
from mailing.services.queueing import queue_email_batch
from mailing.services.resending import requeue_failed_delivery
from mailing.services.status import build_email_batch_status
from mailing.services.attachments import create_existing_document_attachment, create_uploaded_attachment
from mailing.api.renderers import BinaryFileRenderer
from documents.models import Document

logger = logging.getLogger(__name__)


def _ensure_delivery_editable(
    delivery: EmailDelivery,
) -> None:
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



@extend_schema(
    request=EmailBatchCreateSerializer,
    responses={
        201: EmailBatchDetailSerializer,
        400: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
        422: APIErrorResponseSerializer,
    },
    description=(
        "Generate a personalized email batch for the selected students or counselors."
        " The target type is determined by the email purpose."
        " Preview mode creates draft deliveries; automatic mode creates queued deliveries."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def create_email_batch(request):
    serializer = EmailBatchCreateSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    batch = generate_email_batch(
        purpose= serializer.validated_data["purpose"],
        target_ids= serializer.validated_data["target_ids"],
        send_immediately= serializer.validated_data["send_immediately"],
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
    batch = get_object_or_404(
        EmailBatch.objects.prefetch_related("deliveries__student", "deliveries__counselor", "deliveries__attachments"),
        pk=batch_id)

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
    delivery = get_object_or_404(EmailDelivery.objects.select_related("student", "counselor", "batch").prefetch_related("attachments"), pk=delivery_id)

    if request.method == "GET":
        serializer = (EmailDeliveryPreviewSerializer(delivery))

        return Response(serializer.data, status=status.HTTP_200_OK)

    _ensure_delivery_editable(delivery)

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

    batch = EmailBatch.objects.prefetch_related("deliveries__student", "deliveries__counselor", "deliveries__attachments").get(pk=batch.pk)

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
        EmailDelivery.objects.select_related("student", "counselor", "batch").prefetch_related("attachments"), pk= delivery_id
    )

    delivery = requeue_failed_delivery(delivery)

    serializer = EmailDeliveryPreviewSerializer(delivery)

    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)



@extend_schema(
    request=EmailAttachmentUploadSerializer,
    responses={
        201: EmailAttachmentSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Upload an arbitrary file from the "
        "device and attach a snapshot of it "
        "to this email delivery."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def upload_email_attachment(
    request,
    delivery_id,
):
    delivery = get_object_or_404(
        EmailDelivery.objects.select_related(
            "student",
            "counselor",
            "batch",
        ),
        pk=delivery_id,
    )

    _ensure_delivery_editable(
        delivery
    )

    serializer = (
        EmailAttachmentUploadSerializer(
            data=request.data
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    file = serializer.validated_data[
        "file"
    ]

    name = serializer.validated_data.get(
        "name"
    )

    attachment = (
        create_uploaded_attachment(
            delivery=delivery,
            file=file,
            name=name,
        )
    )

    response_serializer = (
        EmailAttachmentSerializer(
            attachment
        )
    )

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )



@extend_schema(
    request=ExistingEmailAttachmentSerializer,
    responses={
        201: EmailAttachmentSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description=(
        "Attach a snapshot of an existing "
        "student or appointment document to "
        "this email delivery. The original "
        "document is not modified."
    ),
    tags=["Mailing"],
)
@api_view(["POST"])
def attach_existing_document_to_email(
    request,
    delivery_id,
):
    delivery = get_object_or_404(
        EmailDelivery.objects.select_related(
            "student",
            "counselor",
            "batch",
        ),
        pk=delivery_id,
    )

    _ensure_delivery_editable(
        delivery
    )

    serializer = (
        ExistingEmailAttachmentSerializer(
            data=request.data
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    document = get_object_or_404(
        Document,
        pk=(
            serializer.validated_data[
                "document_id"
            ]
        ),
    )

    attachment = (
        create_existing_document_attachment(
            delivery=delivery,
            document=document,
        )
    )

    response_serializer = (
        EmailAttachmentSerializer(
            attachment
        )
    )

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )



@extend_schema(
    responses={
        204: OpenApiResponse(
            description="Attachment removed."
        ),
        404: APIErrorResponseSerializer,
        409: APIErrorResponseSerializer,
    },
    description=(
        "Remove an attachment from a draft "
        "or failed email delivery."
    ),
    tags=["Mailing"],
)
@api_view(["DELETE"])
def delete_email_attachment(
    request,
    delivery_id,
    attachment_id,
):
    delivery = get_object_or_404(
        EmailDelivery,
        pk=delivery_id,
    )

    _ensure_delivery_editable(
        delivery
    )

    attachment = get_object_or_404(
        EmailAttachment,
        pk=attachment_id,
        delivery_id=delivery.pk,
    )

    attachment.delete()

    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


@extend_schema(
    responses={
        (
            200,
            "application/octet-stream",
        ): OpenApiTypes.BINARY,
        404: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description=(
        "Download the snapshot currently "
        "attached to an email delivery."
    ),
    tags=["Mailing"],
)
@api_view(["GET"])
@renderer_classes(
    [
        JSONRenderer,
        BinaryFileRenderer,
    ]
)
def download_email_attachment(
    request,
    delivery_id,
    attachment_id,
):
    attachment = get_object_or_404(
        EmailAttachment,
        pk=attachment_id,
        delivery_id=delivery_id,
    )

    if (
        not attachment.file
        or not attachment.file.name
    ):
        raise StoredFileNotFound(
            details={
                "resource_type": (
                    "email_attachment"
                ),
                "resource_id": attachment.pk,
            }
        )

    try:
        file_handle = (
            attachment.file.open("rb")
        )

    except FileNotFoundError as exc:
        raise StoredFileNotFound(
            details={
                "resource_type": (
                    "email_attachment"
                ),
                "resource_id": attachment.pk,
            }
        ) from exc

    except OSError as exc:
        logger.exception(
            (
                "Failed to open email "
                "attachment file"
            ),
            extra={
                "attachment_id": (
                    attachment.pk
                ),
                "delivery_id": (
                    attachment.delivery_id
                ),
            },
        )

        raise FileStorageUnavailable(
            details={
                "resource_type": (
                    "email_attachment"
                ),
                "resource_id": attachment.pk,
            }
        ) from exc

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=attachment.name,
    )


