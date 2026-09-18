from django.db import models

from counselors.models import Counselor
from students.models import Student
from templates.models import Purpose
from documents.models import Document


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

    class RecipientType(models.TextChoices):
        STUDENT = "student", "Student"
        COUNSELOR = "counselor", "Counselor"

    batch = models.ForeignKey(EmailBatch, on_delete=models.CASCADE, related_name="deliveries")

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="email_deliveries", null=True, blank=True)
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE, related_name="email_deliveries", null=True, blank=True)

    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices, default=RecipientType.STUDENT)

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

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(recipient_type="student", student__isnull=False)
                    |
                    models.Q(recipient_type="counselor", counselor__isnull=False)
                ),
                name= "email_delivery_requires_recipient_entity"
            )
        ]

    def __str__(self):
        return (
            f"Email delivery {self.pk}"
            f"to {self.recipient_email}"
        )


class EmailAttachment(models.Model):
    class Source(models.TextChoices):
        EXISTING = "existing", "Existing document"
        UPLOADED = "uploaded", "Uploaded for email"
        GENERATED = "generated", "Generated file"

    delivery = models.ForeignKey(EmailDelivery, on_delete=models.CASCADE, related_name="attachments")

    source = models.CharField(max_length=20, choices=Source.choices)

    source_document = models.ForeignKey(Document, on_delete= models.SET_NULL, null=True, blank=True, related_name="+")

    file = models.FileField(upload_to="mailing/attachments/%Y/%m/", blank=True)

    name = models.CharField(max_length=255)

    content_type = models.CharField(max_length=255, default="application/octet-stream")

    cleaned_at = models.DateTimeField(null=True, blank=True)

    cleanup_error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Attachment {self.pk} for delivery {self.delivery_id}: {self.name}"
    