from django.db import models

# Create your models here.

class Counselor(models.Model):
    title = models.CharField(max_length=10)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    chair = models.CharField(max_length=150, default="Institute")
    
    office_address = models.CharField(max_length=50, help_text="Example: AE22-R273")

    email = models.EmailField(unique=True)
    additional_cc = models.JSONField(default= list, blank=True, help_text="List of additional email addresses")
    #secretary_email = models.EmailField()
    #tertiary_email = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.title} {self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.full_name
    


class Slot(models.Model):

    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE, related_name="slots")

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.counselor} | {self.date} {self.start_time}-{self.end_time}"
    