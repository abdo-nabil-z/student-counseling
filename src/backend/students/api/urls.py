from django.urls import path

from students.api.views import create_list_students

app_name = 'students_api'

#  api/students/

urlpatterns = [
    path("students/", create_list_students, name="create-list-student"),
    
]
