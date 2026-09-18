from django.db import transaction

from appointments.models import Appointment
from counselors.models import Slot
from students.models import Student
from mailing.models import EmailDelivery, EmailBatch, EmailAttachment



@transaction.atomic
def delete_semester_data() -> dict[str, int]:
    """
    Delete data that belongs to the current semester.

    All database deletions succeed together or are rolled back together
    if an exception occurs.
    """
    email_attachments = EmailAttachment.objects.all()
    email_deliveries = EmailDelivery.objects.all()
    email_batches = EmailBatch.objects.all()

    appointments = Appointment.objects.all()
    students = Student.objects.all()
    slots = Slot.objects.all()

    result = {
        "deleted_email_attachments": email_attachments.count(),
        "deleted_email_batches": email_batches.count(),
        "deleted_email_deliveries": email_deliveries.count(),
        "deleted_appointments": appointments.count(),
        "deleted_students": students.count(),
        "deleted_slots": slots.count(),
    }

    email_batches.delete()

    appointments.delete()
    students.delete()
    slots.delete()

    return result