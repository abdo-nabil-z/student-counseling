from django.db import transaction

from appointments.models import Appointment
from counselors.models import Slot
from students.models import Student



@transaction.atomic
def delete_semester_data() -> dict[str, int]:
    """
    Delete data that belongs to the current semester.

    All database deletions succeed together or are rolled back together
    if an exception occurs.
    """
    appointments = Appointment.objects.all()
    students = Student.objects.all()
    slots = Slot.objects.all()

    result = {
        "deleted_appointments": appointments.count(),
        "deleted_students": students.count(),
        "deleted_slots": slots.count(),
    }

    for appointment in appointments:
        appointment.delete()

    for student in students:
        student.delete()

    slots.delete()

    return result