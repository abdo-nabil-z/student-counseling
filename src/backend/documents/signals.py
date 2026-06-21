from django.db.models.signals import post_delete
from django.dispatch import receiver

from documents.models import Document, MasterDocumentVersion


@receiver(post_delete, sender=Document)
def _delete_document_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)


@receiver(post_delete, sender=MasterDocumentVersion)
def _delete_master_version_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
