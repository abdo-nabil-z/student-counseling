import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from documents.models import Document

logger = logging.getLogger(__name__)




def _delete_storage_file(
        storage,
        file_name: str,
        *,
        record_type: str,
        record_id: int | None,
) -> None:

    try:
        storage.delete(file_name)
    except Exception:
        logger.exception(
            "Failed to delete file from storage",
            extra={
                "record_type": record_type,
                "record_id": record_id,
            },
        )


def _schedule_file_deletion(
        file_field,
        *,
        record_type: str,
        record_id: int | None,
) -> None:
    if not file_field or not file_field.name:
        return
    
    storage = file_field.storage
    file_name = file_field.name

    transaction.on_commit(
        lambda: _delete_storage_file(
            storage,
            file_name,
            record_type= record_type,
            record_id=record_id,
        )
    )


@receiver(post_delete, sender=Document)
def delete_document_file_after_commit(
    sender,
    instance,
    **kwargs,
):
    _schedule_file_deletion(
        instance.file,
        record_type="document",
        record_id=instance.pk,
    )


