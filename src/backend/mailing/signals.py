import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from mailing.models import EmailAttachment


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


@receiver(post_delete, sender=EmailAttachment)
def delete_email_attachment_file_after_commit(sender, instance, **kwargs):
    if not instance.file or not instance.file.name:
        return

    storage = instance.file.storage
    file_name = instance.file.name
    attachment_id = instance.pk

    transaction.on_commit(
        lambda: _delete_storage_file(storage, file_name, attachment_id=attachment_id)
    )