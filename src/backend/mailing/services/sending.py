import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from mailing.models import EmailDelivery


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
    delivery.sent_at = timezone.now()

    delivery.save(
        update_fields=[
            "status",
            "last_error",
            "sent_at",
            "updated_at",
        ]
    )


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
                "student_id=%s "
                "attempt=%s"
            ),
            delivery.pk,
            delivery.batch_id,
            delivery.student_id,
            delivery.attempt_count,
            exc_info=True,
        )

        raise

    _record_send_success(delivery)

    logger.info(
        (
            "Email delivery sent successfully: "
            "delivery_id=%s "
            "batch_id=%s "
            "student_id=%s "
            "attempt=%s"
        ),
        delivery.pk,
        delivery.batch_id,
        delivery.student_id,
        delivery.attempt_count,
    )