from django.db import models


class Purpose(models.TextChoices):
    TESTMAIL = "testmail", "Test Mail"
    STUDENT_INVITATION_MAIL = "student_invitation", "Initial Invitation (Student)"
    STUDENT_REMINDER_MAIL = "student_reminder", "Reminder (Student)"
    FORCED_APPOINTMENT_ASSIGNMENT_MAIL = "forced_appointment_assignment", "Forced Appointment Assignment"
    SESSION_INVITATION_MAIL = "session_invitation", "Appointment Invitation"
    COUNSELOR_PREPARATION_INSTRUCTION_MAIL = "counselor_preparation_instruction", "Preparation Instruction (Counselor)"
    SESSION_CANCELLATION_MAIL = "session_cancellation", "Appointment Cancellation"
    
    STUDY_PLAN = "study_plan", "Study Plan"
    SESSION_MINUTES = "session_minutes", "Session Minutes"
    
    


class Template(models.Model):
    name = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TemplatePurpose(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='template_purposes')
    purpose = models.CharField(max_length=50, choices=Purpose.choices)
    default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('template', 'purpose')

    def __str__(self):
        return f"{self.template.name} - {self.purpose}{' (Default)' if self.default else ''}"
    
    
    
