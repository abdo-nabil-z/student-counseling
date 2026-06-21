from django.urls import path
# from counselors.api.views import (
#     create_list_counselors,
#     create_list_counselor_time_slot,
#     detail_counselor,
# )

# app_name = "counselors_api"

# urlpatterns = [
#     path("", create_list_counselors, name="create-list-counselor"),
#     path("<int:counselor_id>/", detail_counselor, name="detail-counselor"),
#     path("<int:counselor_id>/availability-blocks", create_list_counselor_time_slot, name="create-list-counselor-time-slot"),
# ]

from django.urls import path
from counselors.api.views import (
    create_list_counselors,
    create_list_counselor_slots,
    detail_counselor,
)

app_name = "counselors_api"

urlpatterns = [
    path("", create_list_counselors, name="create-list-counselor"),
    path("<int:counselor_id>/", detail_counselor, name="detail-counselor"),
    path("<int:counselor_id>/slots/", create_list_counselor_slots, name="create-list-counselor-slots"),
]