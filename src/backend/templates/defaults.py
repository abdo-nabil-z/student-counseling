"""
Seeds blank Template rows with default content loaded from the `defaults/`
directory at the project root. Invoked once on server startup (see
consultation_backend/wsgi.py and consultation_backend/asgi.py) — never on
every request.
"""
import logging

from django.conf import settings

from templates.models import Purpose, Template

logger = logging.getLogger(__name__)

DEFAULTS_DIR = settings.BASE_DIR / "defaults"

# Maps each purpose to its default content file, relative to DEFAULTS_DIR.
DEFAULT_FILES: dict[str, str] = {
    Purpose.STUDENT_INVITATION_MAIL: "student_invitation.txt",
    Purpose.STUDENT_REMINDER_MAIL: "student_reminder.txt",
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: "forced_appointment_assignment.txt",
    Purpose.APPOINTMENT_INVITATION_MAIL: "appointment_invitation.txt",
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: "counselor_preparation_instruction.txt",
    Purpose.APPOINTMENT_CANCELLATION_MAIL: "appointment_cancellation.txt",
    Purpose.COUNSELOR_AVAILABILITY_REQUEST_MAIL: "counselor_availability_request.txt",
    Purpose.COUNSELOR_APPOINTMENTS_SUMMARY_MAIL: "counselor_appointments_summary.txt",
    Purpose.GENERIC_MAIL: "generic_mail.txt",
    Purpose.STUDY_PLAN: "study_plan.md",
    Purpose.APPOINTMENT_MINUTES: "appointment_minutes.md",
    Purpose.GENERIC_PDF: "generic_pdf.md",
}


def load_default_content(purpose: str) -> str | None:
    """Read the default file mapped to `purpose`. Returns None if unmapped or missing."""
    filename = DEFAULT_FILES.get(purpose)
    if not filename:
        return None

    path = DEFAULTS_DIR / filename
    if not path.is_file():
        logger.warning("Default template file not found for purpose '%s': %s", purpose, path)
        return None

    return path.read_text(encoding="utf-8")


def seed_empty_templates() -> int:
    """Replace every blank (missing/empty/whitespace-only) Template with its default content.

    Returns the number of templates that were updated.
    """
    updated = 0
    for purpose in Purpose.values:
        template, _ = Template.objects.get_or_create(purpose=purpose)
        if template.content.strip():
            continue

        default_content = load_default_content(purpose)
        if default_content is None:
            continue

        template.content = default_content
        template.save(update_fields=["content", "updated_at"])
        updated += 1

    if updated:
        logger.info("Seeded %d empty template(s) with default content.", updated)

    return updated
