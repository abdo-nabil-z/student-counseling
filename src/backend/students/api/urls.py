from django.urls import path
from students.api.views import (
    create_list_students,
    detail_student,
)

app_name = "students_api"

urlpatterns = [
    path("students/", create_list_students, name="create-list-student"),
    path("students/<int:student_id>/", detail_student, name="detail-student"),
]