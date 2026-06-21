from django.urls import path
from students.api.views import (
    create_list_students,
    detail_student,
    get_student_appointment,
    upload_initial_study_plan,
    upload_final_study_plan,
)

app_name = "students_api"

urlpatterns = [
    path("students/", create_list_students, name="create-list-student"),
    path("students/<int:student_id>/", detail_student, name="detail-student"),
    path("students/<int:student_id>/appointment/", get_student_appointment, name="student-appointment"),
    path("students/<int:student_id>/initial-study-plan/", upload_initial_study_plan, name="upload-initial-study-plan"),
    path("students/<int:student_id>/final-study-plan/", upload_final_study_plan, name="upload-final-study-plan"),
]