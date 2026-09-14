from django.db import models

from students.models import Student
from templates.models import Purpose


class EmailBatch(models.Model):
    purpose = models.CharField(max_length=50, choices=Purpose.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return(f"Email batch {self.pk}"
               f"({self.get_purpose_display()})"
               )


class EmailDelivery(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    batch = models.ForeignKey(EmailBatch, on_delete=models.CASCADE, related_name="deliveries")

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="email_deliveries")

    recipient_email = models.EmailField()

    cc = models.JSONField(default=list, blank=True)

    subject = models.CharField(max_length=255)
    body = models.TextField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    attempt_count  = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    next_attempt_at = models.DateTimeField(null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (
            f"Email delivery {self.pk}"
            f"to {self.recipient_email}"
        )