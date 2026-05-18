from django.db import models

# Create your models here.


class Student(models.Model):
    class ContactStatus(models.TextChoices):
        NOT_CONTACTED_YET = "not_contacted_yet", "Not contacted yet"
        EMAILED = 'emailed', 'Emailed'
        CONFIRMED = 'confirmed', 'Confirmed'
        DIDNT_RESPOND = 'didnt_respond', "Didn't respond"
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    user_id = models.CharField(max_length=10)
    #email = models.EmailField()
    
    #todo
    #study_program = models.ForeignKey(StudyProgram, on_delete=models.SET_NULL, null=True)

    enrollment_date = models.DateField(null=True, blank=True)

    contact_status = models.CharField(max_length=30, choices=ContactStatus.choices, default= ContactStatus.NOT_CONTACTED_YET)

    complete_lp = models.IntegerField(default=-1)
    remaining_semesters = models.PositiveBigIntegerField(null=True, blank=True)
    study_path = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.full_name
