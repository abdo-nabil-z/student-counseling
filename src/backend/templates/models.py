from django.db import models


class Purpose(models.TextChoices):
    TESTMAIL = "testmail", "Test Mail"


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
    
    
    
