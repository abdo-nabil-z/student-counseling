from django.db import models

from students.models import Student
from counselors.models import Counselor, Slot

# Create your models here.

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        BOOKED = "booked", "Booked"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        MISSED = "missed", "Missed"

    student = models.OneToOneField(Student, on_delete=models.DO_NOTHING, related_name="appointment")
    counselor = models.ForeignKey(Counselor, on_delete=models.DO_NOTHING, related_name="appointment")

    slot = models.ForeignKey(Slot, on_delete=models.DO_NOTHING, related_name="appointments")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, null=True, blank=True)
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.BOOKED)
   
    minutes = models.ForeignKey(
        'documents.Document', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        docs = [self.minutes]
        super().delete(*args, **kwargs)
        for doc in docs:
            if doc:
                doc.delete()

    def __str__(self):
        return f"{self.student} with {self.counselor} on {self.slot}"
    
