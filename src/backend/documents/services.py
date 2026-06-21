"""
Service functions for creating / attaching documents.
Call these from anywhere in the backend instead of constructing models directly.
"""
from django.core.files.base import File

from documents.models import Document, MasterDocument, MasterDocumentVersion


def attach_document(file: File, name: str) -> Document:
    """Create and persist a Document from an open file-like object."""
    doc = Document(name=name)
    doc.file.save(name, file, save=True)
    return doc


def add_master_version(master: MasterDocument, file: File) -> MasterDocumentVersion:
    """Upload a new version for a MasterDocument."""
    version = MasterDocumentVersion(master=master)
    version.file.save(file.name, file, save=True)
    return version
