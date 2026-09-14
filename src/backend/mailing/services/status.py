from mailing.models import EmailDelivery

def build_email_batch_status(batch)->dict:
    deliveries = list(
        batch.deliveries
        .select_related("student")
        .all()
    )

    counts = {
        EmailDelivery.Status.DRAFT: 0,
        EmailDelivery.Status.QUEUED: 0,
        EmailDelivery.Status.SENT: 0,
        EmailDelivery.Status.FAILED: 0,
    }

    for delivery in deliveries:
        counts[delivery.status] += 1

    return {
        "id": batch.pk,
        "purpose": batch.purpose,
        "total_count": len(deliveries),
        "draft_count": counts[
            EmailDelivery.Status.DRAFT
        ],
        "queued_count": counts[
            EmailDelivery.Status.QUEUED
        ],
        "sent_count": counts[
            EmailDelivery.Status.SENT
        ],
        "failed_count": counts[
            EmailDelivery.Status.FAILED
        ],
        "deliveries": deliveries,
    }