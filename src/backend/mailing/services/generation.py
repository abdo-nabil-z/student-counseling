from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from appointments.models import Appointment
from consultation_backend.api_exceptions import TemplateRenderFailed
from mailing.models import EmailBatch, EmailDelivery
from mailing.subjects import DEFAULT_EMAIL_SUBJECTS
from students.models import Student
from templates.api.render_views import TemplateRenderError, render_from_template
from templates.context_registry import AppointmentStudentCounselorContext, StudentAndBlocksContext
from templates.models import Purpose, Template


STUDENT_ONLY_PURPOSES = {
    Purpose.STUDENT_INVITATION_MAIL,
    Purpose.STUDENT_REMINDER_MAIL,
}


APPOINTMENT_STUDENT_PURPOSES = {
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL,
    Purpose.APPOINTMENT_INVITATION_MAIL,
    Purpose.APPOINTMENT_CANCELLATION_MAIL,
}


COUNSELOR_PURPOSES = {
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL,
}


def _get_appointment(student: Student, purpose: str) -> Appointment:
    appointment = (
        Appointment.objects
        .select_related("counselor")
        .filter(student_id=student.pk)
        .first()
    )

    if appointment is None:
        raise ValidationError(
            {
                "student_ids": [
                    (
                        f"Student {student.pk} does not "
                        f"have na appointment requested "
                        f"for email purpose '{purpose}'."
                    )
                ]
            }
        )

    return appointment


def _build_delivery_context(*, student: Student, purpose: str) -> tuple[dict, str, list[str]]:
    if purpose in STUDENT_ONLY_PURPOSES:
        context = StudentAndBlocksContext.build(student_id=student.pk)

        return (context.model_dump(), student.email,[])

    if(
        purpose in APPOINTMENT_STUDENT_PURPOSES
        or purpose in COUNSELOR_PURPOSES
    ):
        appointment = _get_appointment(student, purpose)

        counselor = appointment.counselor

        context = (
            AppointmentStudentCounselorContext.build(
                student_id=student.pk,
                counselor_id=counselor.pk,
                appointment_id=appointment.pk,
            )
        )

        if purpose in COUNSELOR_PURPOSES:
            return (
                context.model_dump(),
                counselor.email,
                list(
                    counselor.additional_cc or []
                ),
            )

        return (
            context.model_dump(),
            student.email,
            [],
        )

    raise ValidationError(
        {
            "purpose": [
                (
                    f"Purpose '{purpose}' in not "
                    "supported for email generation."
                )
            ]
        }
    )


@transaction.atomic
def generate_email_batch(*, purpose: str, student_ids: list[int],send_immediately: bool)->EmailBatch:
    template = Template.objects.filter(purpose=purpose).first()

    if template is None:
        raise NotFound(
            detail=(
                f"No template exists for "
                f"purpose '{purpose}'."
            ),
            code="email_template_not_found"
        )

    students_by_id = Student.objects.in_bulk(student_ids)

    missing_ids = [
        student_id
        for student_id in student_ids
        if student_id not in students_by_id
    ]

    if missing_ids:
        raise ValidationError(
            {
                "student_ids": [
                    (
                        "The following students do not exist: "
                        + ", ".join(
                            str(student_id)
                            for student_id in missing_ids
                        )
                    )
                ]
            }
        )

    batch = EmailBatch.objects.create(
        purpose=purpose
    )

    delivery_status = (
        EmailDelivery.Status.QUEUED
        if send_immediately
        else EmailDelivery.Status.DRAFT
    )

    for student_id in student_ids:
        student = students_by_id[student_id]

        (context, recipient_email, cc) = _build_delivery_context(student=student, purpose=purpose)

        try:
            rendered_body = render_from_template(template.content, **context)

        except TemplateRenderError as exc:
            raise TemplateRenderFailed(
                details={
                    "purpose": purpose,
                    "student_id": student.pk,
                    **exc.to_dict(),
                }
            ) from exc

        EmailDelivery.objects.create(
            batch=batch,
            student=student,
            recipient_email=recipient_email,
            cc=cc,
            subject=(
                DEFAULT_EMAIL_SUBJECTS[purpose]
            ),
            body=rendered_body,
            status=delivery_status,
        )

    return batch