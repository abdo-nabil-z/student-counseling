from students.models import Student


def mark_student_emailed(student: Student) -> None:
    if student.contact_status == Student.ContactStatus.CONFIRMED:
        return

    student.contact_status = Student.ContactStatus.EMAILED
    student.save(update_fields=["contact_status", "updated_at"])


def mark_student_confirmed(student: Student) -> None:
    if student.contact_status == Student.ContactStatus.CONFIRMED:
        return

    student.contact_status = Student.ContactStatus.CONFIRMED
    student.save(update_fields=["contact_status", "updated_at"])