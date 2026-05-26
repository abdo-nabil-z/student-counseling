from django.urls import path

from counselors.api.views import create_list_counselors, create_list_counselor_time_slot


app_name = 'counselors_api'

#  api/counselors/  or counserlors_api:

urlpatterns = [
    path("", create_list_counselors, name="create-list-counselor"),
    path("<int:counselor_id>/availability-blocks", create_list_counselor_time_slot, name="create-list-counselor-time-slot"),
]
