import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from mailing.models import EmailDelivery, EmailAttachment


logger = logging.getLogger(__name__)


class EmailDeliveryStateError(Exception):
    """
    Raised when an email delivery is not in a state
    that allows it to be sent.
    """

class EmailDeliverySendError(Exception):
    """
    Raised when the email backend reports that the
    message was not sent without raising its own error.
    """

def _record_send_attempt(delivery: EmailDelivery)->None:
    delivery.attempt_count +=1 

    delivery.save(update_fields=["attempt_count", "updated_at"])


def _record_send_failure(delivery: EmailDelivery, error: Exception)->None:
    delivery.last_error = str(error)
    
    delivery.save(update_fields=["last_error", "updated_at"])

def _record_send_success(delivery: EmailDelivery)->None:
    delivery.status = EmailDelivery.Status.SENT
    delivery.last_error = ""
    delivery.next_attempt_at = None
    delivery.sent_at = timezone.now()

    delivery.save(
        update_fields=[
            "status",
            "last_error",
            "next_attempt_at",
            "sent_at",
            "updated_at",
        ]
    )


def _attach_delivery_files(message, delivery: EmailDelivery) -> None:
    for attachment in delivery.attachments.all():
        if attachment.source == EmailAttachment.Source.GENERATED:
            document = attachment.source_document

            if document is None or not document.file or not document.file.name:
                raise FileNotFoundError(
                    f"Generated attachment {attachment.pk} has no stored document."
                )

            document.file.open("rb")
            try:
                content = document.file.read()
            finally:
                document.file.close()

        else:
            if not attachment.file or not attachment.file.name:
                raise FileNotFoundError(
                    f"Email attachment {attachment.pk} has no stored file."
                )

            attachment.file.open("rb")
            try:
                content = attachment.file.read()
            finally:
                attachment.file.close()

        message.attach(
            attachment.name,
            content,
            attachment.content_type or "application/octet-stream",
        )


def _cleanup_attachment_file(attachment: EmailAttachment) -> None:
    if not attachment.file or not attachment.file.name:
        return

    storage = attachment.file.storage
    file_name = attachment.file.name

    storage.delete(file_name)

    attachment.file = ""


def _cleanup_generated_document(attachment: EmailAttachment) -> None:
    document = attachment.source_document

    if document is None:
        return

    if document.file and document.file.name:
        storage = document.file.storage
        file_name = document.file.name

        storage.delete(file_name)

        # Prevent the Document post_delete signal from trying
        # to delete the same physical file again.
        document.file.name = ""

    document.delete()
    attachment.source_document = None



def send_email_delivery_once(delivery: EmailDelivery)->None:
    """
    Attempt to send one queued email delivery exactly once.

    Success:
        QUEUED -> SENT

    Failure:
        - attempt_count is incremented
        - the error is stored in last_error
        - the delivery remains QUEUED
        - the original exception is re-raised

    Retry scheduling is intentionally not handled here.
    The background worker will implement that behavior.
    """

    if delivery.status != EmailDelivery.Status.QUEUED:
        raise EmailDeliveryStateError(
            (
                f"Email delivery {delivery.pk} "
                f"cannot be sent while its status "
                f"is '{delivery.status}'"
            )
        )

    message = EmailMessage(
        subject=delivery.subject,
        body=delivery.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[
            delivery.recipient_email,
        ],
        cc=delivery.cc,
    )

    _record_send_attempt(delivery)

    try:
        _attach_delivery_files(message, delivery)
        sent_count = message.send(fail_silently=False)

        if sent_count != 1:
            raise EmailDeliverySendError(
                (
                    "The email backend did not "
                    "confirm that the message was sent."
                )
            )
    except Exception as exc:
        _record_send_failure(delivery, exc)

        logger.warning(
            (
                "Email delivery failed: "
                "delivery_id=%s "
                "batch_id=%s "
                "recipient_type=%s "
                "student_id=%s "
                "counselor_id=%s "
                "attempt=%s"
            ),
            delivery.pk,
            delivery.batch_id,
            delivery.recipient_type,
            delivery.student_id,
            delivery.counselor_id,
            delivery.attempt_count,
            exc_info=True,
        )

        raise

    _record_send_success(delivery)

    cleanup_sent_delivery_attachments(delivery)

    logger.info(
        (
            "Email delivery sent successfully: "
            "delivery_id=%s "
            "batch_id=%s "
            "recipient_type=%s "
            "student_id=%s "
            "counselor_id=%s "
            "attempt=%s"
        ),
        delivery.pk,
        delivery.batch_id,
        delivery.recipient_type,
        delivery.student_id,
        delivery.counselor_id,
        delivery.attempt_count,
    )



def cleanup_sent_delivery_attachments(delivery: EmailDelivery) -> None:
    try:
        attachments = list(delivery.attachments.select_related("source_document").all())
    except Exception:
        logger.exception(
            "Could not load attachments for post-send cleanup",
            extra={"delivery_id": delivery.pk},
        )
        return

    for attachment in attachments:
        try:
            if attachment.source == EmailAttachment.Source.GENERATED:
                _cleanup_generated_document(attachment)
            else:
                _cleanup_attachment_file(attachment)

            attachment.cleaned_at = timezone.now()
            attachment.cleanup_error = ""
            attachment.save()

        except Exception as exc:
            logger.exception(
                "Failed to clean email attachment after successful send",
                extra={
                    "delivery_id": delivery.pk,
                    "attachment_id": attachment.pk,
                },
            )

            attachment.cleanup_error = str(exc)

            try:
                attachment.save(update_fields=["cleanup_error"])
            except Exception:
                logger.exception(
                    "Failed to record email attachment cleanup error",
                    extra={
                        "delivery_id": delivery.pk,
                        "attachment_id": attachment.pk,
                    },
                )