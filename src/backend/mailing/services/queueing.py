from django.db import transaction
from django.utils import timezone

from mailing.api_exceptions import EmailBatchNotSendable
from mailing.models import EmailDelivery, EmailBatch


@transaction.atomic
def queue_email_batch(batch: EmailBatch)-> int:
    deliveries = (
        batch.deliveries
        .select_for_update()
        .all()
    )

    statuses = set(deliveries.values_list("status",flat=True))

    if not statuses:
        raise EmailBatchNotSendable(
            details={
                "batch_id": batch.pk,
                "reason": "The batch has no emails."
            }
        )

    if statuses != {EmailDelivery.Status.DRAFT}:
        raise EmailBatchNotSendable(
            details={
                "batch_id": batch.pk,
                "current_statuses": sorted(statuses)
            }
        )

    queued_count = deliveries.update(
        status=EmailDelivery.Status.QUEUED,
        updated_at=timezone.now()
    )

    return queued_count