from django.db import transaction

from mailing.api_exceptions import EmailDeliveryNotResendable
from mailing.models import EmailDelivery


@transaction.atomic
def requeue_failed_delivery(delivery: EmailDelivery)->EmailDelivery:
    delivery = (
        EmailDelivery.objects
        .select_for_update()
        .get(pk=delivery.pk)
    )

    if delivery.status != EmailDelivery.Status.FAILED:
        raise EmailDeliveryNotResendable(
            details={
                "delivery_id": delivery.pk,
                "status": delivery.status
            }
        )

    delivery.status = EmailDelivery.Status.QUEUED

    delivery.attempt_count = 0
    delivery.last_error = ""
    delivery.next_attempt_at = None
    delivery.sent_at = None

    delivery.save(
        update_fields=[
            "status",
            "attempt_count",
            "last_error",
            "next_attempt_at",
            "sent_at",
            "updated_at",
        ]
    )

    return delivery