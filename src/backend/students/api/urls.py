from django.urls import path

from students.api.views import create_student

app_name = 'students_api'

urlpatterns = [
    path("create-student/", create_student, name="create-student"),
    
]
