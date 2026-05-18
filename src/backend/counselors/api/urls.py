from django.urls import path

from counselors.api.views import create_counselor, create_counselor_time_slot


app_name = 'counselors_api'


urlpatterns = [
    path("create-counselor/", create_counselor, name="create-counselor"),
    path("create-counselor-time-slot/", create_counselor_time_slot, name="create-counselor-time-slot"),
]
