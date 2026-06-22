from django.db import models


class Document(models.Model):
    """A document attached to a specific entity (Student, Appointment, …)."""
    file = models.FileField(upload_to="documents/%Y/%m/")
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class MasterDocument(models.Model):
    """A reusable document template (e.g. 'Minutes Form') that exists independently
    of any entity and can have multiple versions."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class MasterDocumentVersion(models.Model):
    """One uploaded version of a MasterDocument. Latest by created_at is current."""
    master = models.ForeignKey(MasterDocument, on_delete=models.CASCADE, related_name="versions")
    file = models.FileField(upload_to="master_documents/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.master.name} – {self.created_at:%Y-%m-%d %H:%M}"
