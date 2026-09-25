"""
Bridge between PDF rendering and the documents app, for apps (e.g. emails)
that need a persisted, ID-addressable PDF rather than raw bytes.
"""
from django.core.files.base import ContentFile

from consultation_backend.api_exceptions import TemplateNotConfigured
from documents.services import attach_document
from pdf.rendering import render_template_to_pdf
from templates.models import Template


def save_pdf_as_document(name: str, template_content: str, **context) -> int:
    """Render template_content to PDF, persist it as a Document, and return its id.

    The caller owns the returned Document's lifecycle and is responsible for
    deleting it (e.g. via Document.objects.get(pk=...).delete()) once it's no
    longer needed, such as after successfully sending it by email.
    """
    pdf_bytes = render_template_to_pdf(template_content, **context)

    filename = name if name.lower().endswith(".pdf") else f"{name}.pdf"

    file = ContentFile(pdf_bytes, name=filename)
    document = attach_document(file, filename)
    return document.id

def render_and_save_pdf(name: str, purpose: str, **context) -> int:
    """Render template_content to PDF with a given purpose, persist it as a Document, and return its id.

    The caller owns the returned Document's lifecycle and is responsible for
    deleting it (e.g. via Document.objects.get(pk=...).delete()) once it's no
    longer needed, such as after successfully sending it by email.
    """
    template = Template.objects.filter(purpose=purpose).first()

    if template is None:
        raise TemplateNotConfigured(details={"purpose": purpose})

    return save_pdf_as_document(name, template.content, **context)