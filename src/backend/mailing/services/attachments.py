import logging
import mimetypes
from pathlib import Path

from django.core.files.base import File
from rest_framework.exceptions import ValidationError, APIException

from appointments.models import Appointment
from consultation_backend.api_exceptions import (
    FileStorageUnavailable,
    StoredFileNotFound,
    PdfGenerationFailed,
    TemplateRenderFailed,
)
from pdf.services import render_and_save_pdf
from templates.context_registry import AppointmentMinutesContext, StudyPlanContext
from templates.models import Purpose
from templates.rendering import TemplateRenderError
from documents.models import Document
from mailing.models import EmailAttachment, EmailDelivery
from students.models import Student

logger = logging.getLogger(__name__)


def _guess_content_type(filename: str, supplied_content_type: str | None = None) -> str:
    if supplied_content_type:
        return supplied_content_type

    guess_type, _ = mimetypes.guess_type(filename)

    return guess_type or "application/octet-stream"


def _display_name(requested_name: str | None, fallback_name: str) -> str:
    if requested_name:
        cleaned_name = requested_name.strip()

        if cleaned_name:
            return cleaned_name

    return Path(fallback_name).name


def _delete_failed_upload(attachment: EmailAttachment) -> None:
    if not attachment.file or not attachment.file.name:
        return

    try:
        attachment.file.storage.delete(attachment.file.name)

    except Exception:
        logger.exception("Failed to clean up email attachment after save error")


def _save_attachment(*, attachment: EmailAttachment, file: File, storage_filename: str) -> EmailAttachment:
    try:
        attachment.file.save(
            Path(storage_filename).name,
            file,
            save=False,
        )

        attachment.save()
    except Exception:
        _delete_failed_upload(attachment)
        raise

    return attachment

def _allowed_document_ids(delivery: EmailDelivery) -> set[int]:
    if delivery.student_id is None:
        return set()

    student_data = (
        Student.objects.filter(pk=delivery.student_id)
        .values("initial_study_plan_id", "final_study_plan_id")
        .first()
    )

    if student_data is None:
        return set()

    document_ids = {
        document_id
        for document_id in [
            student_data[
                "initial_study_plan_id"
            ],
            student_data[
                "final_study_plan_id"
            ],
        ]
        if document_id is not None
    }

    minutes_id = (
        Appointment.objects.filter(student_id=delivery.student_id)
                            .values_list("minutes_id", flat=True)
                            .first()
    )

    if minutes_id is not None:
        document_ids.add(minutes_id)

    return document_ids


def _pdf_name(requested_name: str | None, default_name: str):
    if requested_name:
        name = requested_name.strip()

        if name:
            if name.lower().endswith(".pdf"):
                name = name[:-4]

            return name

    return default_name


def _build_generated_pdf_context(*, delivery: EmailDelivery, purpose: str) -> tuple[dict, str]:
    if delivery.student_id is None:
        raise ValidationError({
            "purpose": ["This PDF requires an email delivery with a student context."]
        })

    if purpose == Purpose.STUDY_PLAN:
        context = StudyPlanContext.build(student_id=delivery.student_id)

        default_name = f"study-plan-{delivery.student_id}"

        return context.model_dump(), default_name

    if purpose == Purpose.APPOINTMENT_MINUTES:
        appointment = Appointment.objects.select_related("counselor").filter(student_id=delivery.student_id).first()

        if appointment is None:
            raise ValidationError({
                "purpose": ["Appointment minutes cannot be generated because this student does not have an appointment."]
            })

        context = (
            AppointmentMinutesContext.build(
                student_id=(
                    delivery.student_id
                ),
                counselor_id=(
                    appointment.counselor_id
                ),
                appointment_id=(
                    appointment.pk
                ),
            )
        )
        default_name = (
            f"appointment-minutes-"
            f"{delivery.student_id}"
        )

        return (
            context.model_dump(),
            default_name,
        )
    raise ValidationError(
        {
            "purpose": [
                (
                    f"'{purpose}' is not a "
                    f"supported PDF attachment "
                    f"purpose."
                )
            ]
        }
    )


def create_uploaded_attachment(*, delivery: EmailDelivery, file, name: str | None = None) -> EmailAttachment:
    filename = Path(file.name).name

    attachment = EmailAttachment(
        delivery=delivery,
        source=(
            EmailAttachment.Source.UPLOADED
        ),
        name=_display_name(
            name,
            filename,
        ),
        content_type=_guess_content_type(
            filename,
            getattr(
                file,
                "content_type",
                None,
            ),
        ),
    )

    return _save_attachment(
        attachment=attachment,
        file=file,
        storage_filename=filename,
    )


def create_existing_document_attachment(
    *,
    delivery: EmailDelivery,
    document: Document,
) -> EmailAttachment:
    allowed_ids = _allowed_document_ids(
        delivery
    )

    if document.pk not in allowed_ids:
        raise ValidationError(
            {
                "document_id": [
                    (
                        "This document is not "
                        "associated with the student "
                        "or appointment context of "
                        "this email delivery."
                    )
                ]
            }
        )

    duplicate_exists = (
        EmailAttachment.objects
        .filter(
            delivery=delivery,
            source_document=document,
        )
        .exists()
    )

    if duplicate_exists:
        raise ValidationError(
            {
                "document_id": [
                    (
                        "This document is already "
                        "attached to this email."
                    )
                ]
            }
        )

    if (
        not document.file
        or not document.file.name
    ):
        raise StoredFileNotFound(
            details={
                "resource_type": "document",
                "resource_id": document.pk,
            }
        )

    filename = Path(
        document.file.name
    ).name

    attachment = EmailAttachment(
        delivery=delivery,
        source=(
            EmailAttachment.Source.EXISTING
        ),
        source_document=document,
        name=document.name,
        content_type=_guess_content_type(
            filename
        ),
    )

    try:
        document.file.open("rb")

    except FileNotFoundError as exc:
        raise StoredFileNotFound(
            details={
                "resource_type": "document",
                "resource_id": document.pk,
            }
        ) from exc

    except OSError as exc:
        logger.exception(
            (
                "Failed to open document while "
                "creating email attachment snapshot"
            ),
            extra={
                "document_id": document.pk,
                "delivery_id": delivery.pk,
            },
        )

        raise FileStorageUnavailable(
            details={
                "resource_type": "document",
                "resource_id": document.pk,
            }
        ) from exc

    try:
        snapshot_file = File(
            document.file.file,
            name=filename,
        )

        return _save_attachment(
            attachment=attachment,
            file=snapshot_file,
            storage_filename=filename,
        )

    finally:
        document.file.close()


def create_generated_pdf_attachment(
    *,
    delivery: EmailDelivery,
    purpose: str,
    name: str | None = None,
) -> EmailAttachment:
    context, default_name = (
        _build_generated_pdf_context(
            delivery=delivery,
            purpose=purpose,
        )
    )

    pdf_name = _pdf_name(
        name,
        default_name,
    )

    try:
        document_id = render_and_save_pdf(
            name=pdf_name,
            purpose=purpose,
            **context,
        )

    except TemplateRenderError as exc:
        raise TemplateRenderFailed(
            details={
                "purpose": purpose,
                **exc.to_dict(),
            }
        ) from exc

    except APIException:
        raise

    except Exception as exc:
        logger.exception(
            (
                "PDF generation failed for "
                "email attachment"
            ),
            extra={
                "delivery_id": delivery.pk,
                "purpose": purpose,
            },
        )

        raise PdfGenerationFailed(
            details={
                "purpose": purpose,
                "delivery_id": delivery.pk,
            }
        ) from exc

    document = Document.objects.get(
        pk=document_id
    )

    try:
        attachment = (
            EmailAttachment.objects.create(
                delivery=delivery,
                source=(
                    EmailAttachment
                    .Source
                    .GENERATED
                ),
                source_document=document,
                name=f"{pdf_name}.pdf",
                content_type=(
                    "application/pdf"
                ),
            )
        )

    except Exception:
        # The PDF was created, but attaching
        # it to the delivery failed.
        #
        # Do not leave an orphan Document.
        document.delete()
        raise

    return attachment