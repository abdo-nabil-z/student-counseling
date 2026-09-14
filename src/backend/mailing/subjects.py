from templates.models import Purpose


DEFAULT_EMAIL_SUBJECTS = {
    Purpose.STUDENT_INVITATION_MAIL: (
        "Invitation to student counseling"
    ),
    Purpose.STUDENT_REMINDER_MAIL: (
        "Reminder: student counseling"
    ),
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: (
        "Counseling appointment assignment"
    ),
    Purpose.APPOINTMENT_INVITATION_MAIL: (
        "Counseling appointment"
    ),
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: (
        "Counseling preparation instructions"
    ),
    Purpose.APPOINTMENT_CANCELLATION_MAIL: (
        "Counseling appointment cancelled"
    )
}