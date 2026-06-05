from pydantic import BaseModel

from students.models import Student


class StudentContext(BaseModel):
    matriculation_number: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    course_of_studies: str
    current_study_semester: int
    credit_points: int
    contact_status: str

    @classmethod
    def from_model(cls, student: Student) -> "StudentContext":
        return cls(
            matriculation_number=student.matriculation_number,
            first_name=student.first_name,
            last_name=student.last_name,
            full_name=student.full_name,
            email=student.email,
            course_of_studies=student.course_of_studies or "",
            current_study_semester=student.current_study_semester or 0,
            credit_points=student.credit_points,
            contact_status=student.contact_status,
        )
