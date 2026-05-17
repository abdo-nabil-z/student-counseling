from django.db import models

from students.models import Student
from counselors.models import Counselor, AvailabilitySlot

# Create your models here.

class CounselingSession(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        BOOKED = "booked", "Booked"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        MISSED = "missed", "Missed"
    
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, related_name="counseling_session")
    counselor = models.ForeignKey(Counselor, on_delete=models.DO_NOTHING, related_name="counseling_session")

    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.DO_NOTHING, related_name="session")

    notes = models.CharField(max_length=300, null=True, blank=True) # URL for the directory where the pdf el saved

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.BOOKED)

    initial_study_plan = models.CharField(max_length=300, null=True, blank=True)# URL for the directory where the pdf el saved
    final_study_plan = models.CharField(max_length=300, null=True, blank=True)# URL for the directory where the pdf el saved

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} with {self.counselor} on {self.session_date}"
    
