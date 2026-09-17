import logging
import mimetypes
from pathlib import Path

from django.core.files.base import File
from rest_framework.exceptions import ValidationError

from appointments.models import Appointment
from consultation_backend.api_exceptions import FileStorageUnavailable, StoredFileNotFound
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