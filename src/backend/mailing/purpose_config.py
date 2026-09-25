from dataclasses import dataclass
from typing import Literal

from templates.models import Purpose


TargetType = Literal[
    "student",
    "counselor",
    "external",
]

ContextKind = Literal[
    "student",
    "appointment",
    "counselor",
    "counselor_appointments",
    "external",
]


@dataclass(frozen=True)
class EmailPurposeConfig:
    target_type: TargetType
    recipient_type: TargetType
    context_kind: ContextKind


EMAIL_PURPOSE_CONFIG  = {
    Purpose.STUDENT_INVITATION_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="student",
            context_kind="student",
        )
    ),

    Purpose.STUDENT_REMINDER_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="student",
            context_kind="student",
        )
    ),

    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="student",
            context_kind="appointment",
        )
    ),

    Purpose.APPOINTMENT_INVITATION_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="student",
            context_kind="appointment",
        )
    ),

    Purpose.APPOINTMENT_CANCELLATION_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="student",
            context_kind="appointment",
        )
    ),

    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: (
        EmailPurposeConfig(
            target_type="student",
            recipient_type="counselor",
            context_kind="appointment",
        )
    ),

    Purpose.COUNSELOR_AVAILABILITY_REQUEST_MAIL: (
        EmailPurposeConfig(
            target_type="counselor",
            recipient_type="counselor",
            context_kind="counselor",
        )
    ),

    Purpose.COUNSELOR_APPOINTMENTS_SUMMARY_MAIL: (
        EmailPurposeConfig(
            target_type="counselor",
            recipient_type="counselor",
            context_kind="counselor_appointments",
        )
    ),

    Purpose.GENERAL_MAIL:EmailPurposeConfig(
        target_type="external",
        recipient_type="external",
        context_kind="external",
    ),
}


EMAIL_PURPOSE_CHOICES = [
    (
        purpose,
        purpose.label,
    )
    for purpose in EMAIL_PURPOSE_CONFIG
]