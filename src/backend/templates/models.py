from django.db import models


class Purpose(models.TextChoices):
    STUDENT_INVITATION_MAIL = "student_invitation", "Initial Invitation (Student)"
    STUDENT_REMINDER_MAIL = "student_reminder", "Reminder (Student)"
    FORCED_APPOINTMENT_ASSIGNMENT_MAIL = "forced_appointment_assignment", "Forced Appointment Assignment"
    APPOINTMENT_INVITATION_MAIL = "appointment_invitation", "Appointment Invitation"
    COUNSELOR_PREPARATION_INSTRUCTION_MAIL = "counselor_preparation_instruction", "Preparation Instruction (Counselor)"
    APPOINTMENT_CANCELLATION_MAIL = "appointment_cancellation", "Appointment Cancellation"
    COUNSELOR_AVAILABILITY_REQUEST_MAIL = "counselor_availability_request", "Availability Request (Counselor)"
    COUNSELOR_APPOINTMENTS_SUMMARY_MAIL = "counselor_appointments_summary", "Accepted Appointments Summary (Counselor)"
    GENERAL_MAIL = "general_mail", "General Email"

    STUDY_PLAN = "study_plan", "Study Plan"
    APPOINTMENT_MINUTES = "appointment_minutes", "Appointment Minutes"


class Template(models.Model):
    purpose = models.CharField(max_length=50, choices=Purpose.choices, unique=True)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_purpose_display()
    
    
    
