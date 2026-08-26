from django.urls import path

from mailing.api.views import create_email_batch, email_delivery_detail, get_email_batch, send_email_batch


app_name = "mailing_api"


urlpatterns = [
    path("batches/", create_email_batch, name="create-email-batch"),
    path("batches/<int:batch_id>/", get_email_batch, name="email-batch-detail"),
    path("batches/<int:batch_id>/send/", send_email_batch, name="send-email-batch"),
    path("deliveries/<int:delivery_id>/", email_delivery_detail, name="email-delivery-detail"),
]