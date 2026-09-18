import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from mailing.models import EmailAttachment
from documents.models import Document


logger = logging.getLogger(__name__)


def _delete_storage_file(storage, file_name: str, *, attachment_id: int | None) -> None:
    try:
        storage.delete(file_name)
    except Exception:
        logger.exception(
            (
                "Failed to delete email attachment "
                "file from storage"
            ),
            extra={
                "attachment_id": attachment_id,
            },
        )


def _delete_generated_document(
    document_id: int,
) -> None:
    try:
        document = (
            Document.objects
            .filter(
                pk=document_id
            )
            .first()
        )

        if document is not None:
            document.delete()

    except Exception:
        logger.exception(
            (
                "Failed to delete generated "
                "email PDF document"
            ),
            extra={
                "document_id": document_id,
            },
        )


@receiver(post_delete, sender=EmailAttachment)
def delete_email_attachment_file_after_commit(sender, instance, **kwargs):
    if instance.file and instance.file.name:

        storage = instance.file.storage
        file_name = instance.file.name
        attachment_id = instance.pk

        transaction.on_commit(
            lambda: _delete_storage_file(storage, file_name, attachment_id=attachment_id)
        )

    if (
        instance.source
        == EmailAttachment.Source.GENERATED
        and instance.source_document_id
        is not None
    ):
        document_id = (
            instance.source_document_id
        )

        transaction.on_commit(
            lambda: (
                _delete_generated_document(
                    document_id
                )
            )
        )