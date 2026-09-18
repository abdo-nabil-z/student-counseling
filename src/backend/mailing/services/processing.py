import logging
import smtplib
import socket
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from mailing.models import EmailDelivery
from mailing.services.sending import send_email_delivery_once


logger = logging.getLogger(__name__)


def _is_temporary_smtp_code(code: int)->bool:
    return 400 <= code <500


def _recipients_refused_is_retryable(exception: smtplib.SMTPRecipientsRefused)->bool:
    """
    SMTPRecipientsRefused stores errors as:

        {
            "email@example.com": (
                450,
                b"Mailbox temporarily unavailable"
            )
        }

    Retry if at least one refusal is temporary (4xx).
    """

    for error in exception.recipients.values():
        code = error[0]

        if _is_temporary_smtp_code(code):
            return True

    return False


def is_retryable_email_error(exception: Exception)->bool:
    """
    Determine whether an email failure is likely temporary.

    Temporary examples:
    - SMTP server disconnected
    - connection timeout
    - SMTP 4xx response

    Permanent examples:
    - invalid recipient (5xx)
    - authentication failure (5xx)
    - unsupported SMTP operation
    """

    if isinstance(exception, smtplib.SMTPRecipientsRefused):
        return _recipients_refused_is_retryable(exception)

    if isinstance(exception, smtplib.SMTPResponseException):
        return _is_temporary_smtp_code(exception.smtp_code)

    if isinstance(exception,(smtplib.SMTPServerDisconnected,
                            socket.timeout,
                            TimeoutError,
                            ConnectionError)):
        return True

    if isinstance(exception, OSError):
        return True

    return False


def _schedule_retry(delivery: EmailDelivery)->None:
    delivery.status = EmailDelivery.Status.QUEUED

    delivery.next_attempt_at = (
        timezone.now()
        + timedelta(
            seconds=(settings.EMAIL_RETRY_DELAY_SECONDS)
        )
    )

    delivery.save(
        update_fields=[
            "status",
            "next_attempt_at",
            "updated_at",
        ]
    )

    logger.info(
        (
            "Email delivery retry scheduled: "
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


def _mark_failed(delivery: EmailDelivery)->None:
    delivery.status = EmailDelivery.Status.FAILED
    delivery.next_attempt_at = None

    delivery.save(
        update_fields=[
            "status",
            "next_attempt_at",
            "updated_at",
        ]
    )

    logger.error(
        (
            "Email delivery permanently failed: "
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


def process_email_delivery(delivery: EmailDelivery)->None:
    """
    Process one queued email.

    Success:
        QUEUED -> SENT

    Retryable first failure:
        QUEUED -> QUEUED
        next_attempt_at is scheduled

    Permanent failure or exhausted retries:
        QUEUED -> FAILED
    """
    try:
        send_email_delivery_once(delivery)

    except Exception as exc:
        delivery.refresh_from_db()

        retryable = is_retryable_email_error(exc)

        attempts_remaining = (
            delivery.attempt_count < settings.EMAIL_MAX_SEND_ATTEMPTS
        )

        if retryable and attempts_remaining:
            _schedule_retry(delivery)
            return

        _mark_failed(delivery)


def get_next_ready_delivery():
    """
    Return the next queued delivery that is ready
    for an initial attempt or scheduled retry.
    """
    now = timezone.now()

    return (
        EmailDelivery.objects
        .filter(
            status=EmailDelivery.Status.QUEUED
        )
        .filter(
            Q(next_attempt_at__isnull=True)| Q(next_attempt_at__lte=now)
        )
        .select_related(
            "batch",
            "student",
            "counselor",
        )
        .prefetch_related(
            "attachments__source_document"
        )
        .order_by(
            "created_at",
            "id"
        )
        .first()
    )


def process_next_queued_delivery()->bool:
    """
    Process one ready delivery.

    Returns:
        True if an email was processed.
        False if no email is currently ready.
    """
    delivery = get_next_ready_delivery()

    if delivery is None:
        return False

    process_email_delivery(delivery)

    return True