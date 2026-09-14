from django.db import models


class Document(models.Model):
    """A document attached to a specific entity (Student, Appointment, …)."""
    file = models.FileField(upload_to="documents/%Y/%m/")
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
