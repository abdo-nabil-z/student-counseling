from django.db import models

# Create your models here.

class Counselor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    user_id = models.CharField(max_length=10)
    #email = models.EmailField(blank=True)
    
    department = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.full_name
    


class AvailabilitySlot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
    
    counselor = models.ForeignKey(Counselor, on_delete=models.CASCADE, related_name="availability_slots")
    
    start_time = models.DateTimeField()
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self):
        return f"{self.counselor} - {self.start}"