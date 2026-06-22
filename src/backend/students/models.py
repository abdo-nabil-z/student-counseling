from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

matriculation_number_validator = RegexValidator(regex=r"^\d+$", message="Only numbers are allowed.")

class Student(models.Model):
    class ContactStatus(models.TextChoices):
        NOT_CONTACTED_YET = "not_contacted_yet", "Not contacted yet"
        EMAILED = 'emailed', 'Emailed'
        CONFIRMED = 'confirmed', 'Confirmed'
        DIDNT_RESPOND = 'didnt_respond', "Didn't respond"
    
    matriculation_number = models.CharField(max_length=9,unique=True, validators=[matriculation_number_validator])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=101)

    #user_id = models.CharField(max_length=10)
    email = models.EmailField()
    
    course_of_studies = models.CharField(null=True, blank=True)
    current_study_semester = models.PositiveSmallIntegerField(null=True, blank=True)
    credit_points = models.PositiveIntegerField(null=True, blank=True)
    
    #study_program = models.ForeignKey(StudyProgram, on_delete=models.SET_NULL, null=True)

    contact_status = models.CharField(max_length=30, choices=ContactStatus.choices, default= ContactStatus.NOT_CONTACTED_YET)

    
    initial_study_plan = models.ForeignKey(
        'documents.Document', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    final_study_plan = models.ForeignKey(
        'documents.Document', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    #study_path = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        docs = [self.initial_study_plan, self.final_study_plan]
        super().delete(*args, **kwargs)
        for doc in docs:
            if doc:
                doc.delete()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.full_name
