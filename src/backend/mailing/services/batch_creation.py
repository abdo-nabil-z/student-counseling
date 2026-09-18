from mailing.models import EmailBatch
from mailing.services.attachments import (
    create_existing_document_attachment,
    create_generated_pdf_attachment,
    create_uploaded_attachment,
    get_existing_document_for_delivery,
)
from mailing.services.generation import generate_email_batch
from mailing.services.queueing import queue_email_batch


def create_email_batch_with_attachments(
    *,
    purpose: str,
    target_ids: list[int],
    send_immediately: bool,
    generated_pdf_purposes: list[str],
    existing_document_types: list[str],
    uploaded_files: list,
) -> EmailBatch:
    # Always create drafts first.
    # This prevents the queue worker from picking up the email
    # before its attachments have been created.
    batch = generate_email_batch(
        purpose=purpose,
        target_ids=target_ids,
        send_immediately=False,
    )

    try:
        deliveries = list(
            batch.deliveries.select_related("student", "counselor", "batch").all()
        )

        for delivery in deliveries:
            for document_type in existing_document_types:
                document = get_existing_document_for_delivery(delivery, document_type)
                create_existing_document_attachment(delivery=delivery, document=document)

            for pdf_purpose in generated_pdf_purposes:
                create_generated_pdf_attachment(
                    delivery=delivery,
                    purpose=pdf_purpose,
                )

            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                create_uploaded_attachment(
                    delivery=delivery,
                    file=uploaded_file,
                )

        if send_immediately:
            queue_email_batch(batch)

        return batch

    except Exception:
        batch.delete()
        raise