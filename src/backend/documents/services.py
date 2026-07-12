"""
Service functions for creating / attaching documents.
Call these from anywhere in the backend instead of constructing models directly.
"""
import logging

from django.db import models, transaction
from django.core.files.base import File

from documents.models import Document, MasterDocument, MasterDocumentVersion

logger = logging.getLogger(__name__)


def attach_document(file: File, name: str) -> Document:
    """Create and persist a Document from an open file-like object."""
    document = Document(name=name)
    
    try:
        document.file.save(file.name, file, save=False)
        document.save()
    except Exception:
        _delete_uploaded_file(
            document.file,
            record_type="document"
        )
        raise
    
    return document


def add_master_version(master: MasterDocument, file: File) -> MasterDocumentVersion:
    """Upload a new version for a MasterDocument."""
    version = MasterDocumentVersion(master=master)
    
    try:
        version.file.save(file.name, file, save=False)
        version.save()
    
    except Exception:
        _delete_uploaded_file(version.file, record_type="master_document_version")
        raise
    
    return version


def _delete_uploaded_file(
        file_field,
        *,
        record_type: str,
) -> None:
    if not file_field or not file_field.name:
        return
    
    try:
        file_field.storage.delete(file_field.name)
    except Exception:
        logger.exception(
            "Failed to clean up an uploaded file after a database error",
            extra={
                "record_type": record_type,
            }
        )


def replace_attached_document(
        instance: models.Model,
        field_name: str,
        file: File,
        name: str,
) -> Document:
    old_document = getattr(instance, field_name)
    new_document = None

    try:
        with transaction.atomic():
            new_document = attach_document(file=file, name=name)

            setattr(instance, field_name, new_document)

            instance.save(update_fields=[field_name])

            if old_document is not None:
                old_document.delete()

    except Exception:
        setattr(instance, field_name, old_document)
        if new_document is not None:
            _delete_uploaded_file(new_document.file, record_type="document")
        
        raise
    
    return new_document

