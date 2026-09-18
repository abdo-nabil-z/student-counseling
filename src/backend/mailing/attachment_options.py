from templates.models import Purpose


GENERATED_PDF_PURPOSE_CHOICES = [
    (Purpose.STUDY_PLAN, Purpose.STUDY_PLAN.label),
    (Purpose.APPOINTMENT_MINUTES, Purpose.APPOINTMENT_MINUTES.label),
]


EXISTING_DOCUMENT_TYPE_CHOICES = [
    ("initial_study_plan", "Initial study plan"),
    ("final_study_plan", "Final study plan"),
    ("appointment_minutes", "Appointment minutes"),
]