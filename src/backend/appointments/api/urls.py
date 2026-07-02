from django.urls import path
from appointments.api.views import create_appointment, list_appointments, detail_update_appointment, upload_appointment_minutes

app_name = "appointments_api"

urlpatterns = [
    path("", list_appointments, name="list-appointments"),
    path("create-appointment/", create_appointment, name="create-appointment"),
    path("<int:appointment_id>/", detail_update_appointment, name="detail-update-appointment"),
    path("<int:appointment_id>/minutes/", upload_appointment_minutes, name="upload-minutes"),
]