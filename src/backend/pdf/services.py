"""
Bridge between PDF rendering and the documents app, for apps (e.g. emails)
that need a persisted, ID-addressable PDF rather than raw bytes.
"""
from django.core.files.base import ContentFile

from documents.services import attach_document
from pdf.rendering import render_purpose_to_pdf


def save_pdf_as_document(name: str, template_content: str, **context) -> int:
    """Render template_content to PDF, persist it as a Document, and return its id.

    The caller owns the returned Document's lifecycle and is responsible for
    deleting it (e.g. via Document.objects.get(pk=...).delete()) once it's no
    longer needed, such as after successfully sending it by email.
    """
    pdf_bytes = render_purpose_to_pdf(template_content, **context)
    file = ContentFile(pdf_bytes, name=f"{name}.pdf")
    document = attach_document(file, name)
    return document.id
