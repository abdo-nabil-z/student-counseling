from django.db import transaction
from rest_framework.exceptions import ValidationError

from appointments.models import Appointment
from consultation_backend.api_exceptions import TemplateRenderFailed, TemplateNotConfigured
from mailing.models import EmailBatch, EmailDelivery
from mailing.subjects import DEFAULT_EMAIL_SUBJECTS
from mailing.api_exceptions import EmailTemplateNotConfigured
from mailing.purpose_config import EMAIL_PURPOSE_CONFIG
from mailing.subjects import DEFAULT_EMAIL_SUBJECTS
from students.models import Student
from templates.rendering import TemplateRenderError, render_from_template
from templates.context_registry import (
    AppointmentStudentCounselorContext, 
    StudentAndBlocksContext,
    CounselorAppointmentsContext,
    CounselorOnlyContext,
    ExternalRecipientContext,
)
from templates.models import Template
from counselors.models import Counselor




def _get_appointment(*, student: Student, purpose: str) -> Appointment:
    appointment = (
        Appointment.objects
        .select_related("counselor")
        .filter(student_id=student.pk)
        .first()
    )

    if appointment is None:
        raise ValidationError(
            {
                "target_ids": [
                    (
                        f"Student {student.pk} does not "
                        f"have na appointment requested "
                        f"for email purpose '{purpose}'."
                    )
                ]
            }
        )

    return appointment


def _build_student_target(*, student: Student, purpose: str):
    config = EMAIL_PURPOSE_CONFIG[purpose]

    if config.context_kind == "student":
        context = StudentAndBlocksContext.build(student_id=student.pk)

        return (context.model_dump(), student, None, student.email, [])

    if config.context_kind == "appointment":
        appointment = _get_appointment(student=student, purpose=purpose)

        counselor = appointment.counselor

        context = (
            AppointmentStudentCounselorContext.build(
                student_id=student.pk,
                counselor_id=counselor.pk,
                appointment_id=appointment.pk,
            )
        )

        if config.recipient_type == EmailDelivery.RecipientType.COUNSELOR:
            recipient_email = counselor.email
            cc = list(counselor.additional_cc or [])

        else:
            recipient_email = student.email
            cc = []

        return (
            context.model_dump(),
            student,
            counselor,
            recipient_email,
            cc,
        )

    raise ValidationError(
        {
            "purpose": [
                (
                    f"Purpose '{purpose}' has an invalid student context configuration."
                )
            ]
        }
    )


def _build_counselor_target(*, counselor: Counselor, purpose: str):
    config = EMAIL_PURPOSE_CONFIG[purpose]

    if config.context_kind == "counselor":
        context = CounselorOnlyContext.build(counselor_id=counselor.pk)

    elif config.context_kind == "counselor_appointments":
        context = CounselorAppointmentsContext.build(counselor_id=counselor.pk)

    else:
        raise ValidationError(
            {
                "purpose": [
                        f"Purpose '{purpose}' has an invalid counselor context configuration."
                ]
            }
        )

    return(
        context.model_dump(),
        None,
        counselor,
        counselor.email,
        list(counselor.additional_cc or [])
    )


def _build_external_target(*, recipient_email: str):
    context = ExternalRecipientContext.build(recipient_email=recipient_email)

    return (
        context.model_dump(),
        None,
        None,
        recipient_email,
        [],
    )


def _load_targets(*, purpose: str, target_ids: list[int]):
    config = EMAIL_PURPOSE_CONFIG[purpose]

    if config.target_type == "student":
        targets_by_id = Student.objects.in_bulk(target_ids)

    elif config.target_type == "counselor":
        targets_by_id = Counselor.objects.in_bulk(target_ids)

    else:
        return {}

    missing_ids = [
        target_id
        for target_id in target_ids
        if target_id not in targets_by_id
    ]

    if missing_ids:
        raise ValidationError({
            "target_ids": [
                "The following targets do not exist: "
                + ", ".join(str(target_id) for target_id in missing_ids)
            ]
        })

    return targets_by_id

@transaction.atomic
def generate_email_batch(*, purpose: str, target_ids: list[int], external_recipients=None, send_immediately: bool)->EmailBatch:
    external_recipients = external_recipients or []

    config = EMAIL_PURPOSE_CONFIG.get(purpose)

    if config is None:
        raise ValidationError(
            {
                "purpose": [
                    (
                        f"Purpose '{purpose}' is "
                        f"not supported for email "
                        f"generation."
                    )
                ]
            }
        )

    template = Template.objects.filter(purpose=purpose).first()

    if template is None:
        raise EmailTemplateNotConfigured(
            details={
                "purpose": purpose,
            }
        )

    targets_by_id  = _load_targets(purpose=purpose, target_ids=target_ids)

    batch = EmailBatch.objects.create(
        purpose=purpose
    )

    delivery_status = (
        EmailDelivery.Status.QUEUED
        if send_immediately
        else EmailDelivery.Status.DRAFT
    )

    if config.target_type == "external":
        target_values = external_recipients
    else:
        target_values = target_ids


    for target_value in target_values:
        if config.target_type == "student":
            context, student, counselor, recipient_email, cc = _build_student_target(
                student=targets_by_id[target_value],
                purpose=purpose,
            )

        elif config.target_type == "counselor":
            context, student, counselor, recipient_email, cc = _build_counselor_target(
                counselor=targets_by_id[target_value],
                purpose=purpose,
            )

        else:
            context, student, counselor, recipient_email, cc = _build_external_target(
                recipient_email=target_value
            )

        try:
            rendered_body = render_from_template(template.content, **context)
        except TemplateRenderError as exc:
            raise TemplateRenderFailed(details={
                "purpose": purpose,
                "target_type": config.target_type,
                "target": target_value,
                **exc.to_dict(),
            }) from exc

        EmailDelivery.objects.create(
            batch=batch,
            recipient_type=config.recipient_type,
            student=student,
            counselor=counselor,
            recipient_email=recipient_email,
            cc=cc,
            subject=DEFAULT_EMAIL_SUBJECTS[purpose],
            body=rendered_body,
            status=delivery_status,
        )

    return batch