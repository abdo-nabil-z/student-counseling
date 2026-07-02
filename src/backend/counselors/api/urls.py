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
    get_counselor_slot_status,
    list_all_counselor_slot_statuses,
)

app_name = "counselors_api"

urlpatterns = [
    path("", create_list_counselors, name="create-list-counselor"),
    
    path("slot-status/", list_all_counselor_slot_statuses, name="list-all-counselor-slot-statuses"),
    
    path("<int:counselor_id>/", detail_counselor, name="detail-counselor"),
    path("<int:counselor_id>/slots/", create_list_counselor_slots, name="create-list-counselor-slots"),
    path("<int:counselor_id>/slot-status/", get_counselor_slot_status, name="counselor-slot-status"),
]