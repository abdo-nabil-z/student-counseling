from django.urls import path

from mailing.api.views import (
    create_email_batch,
    email_delivery_detail,
    get_email_batch,
    send_email_batch,
    get_email_batch_status,
    resend_email_delivery,
    attach_existing_document_to_email,
    delete_email_attachment,
    download_email_attachment,
    upload_email_attachment,
)

app_name = "mailing_api"


urlpatterns = [
    path("batches/", create_email_batch, name="create-email-batch"),
    path("batches/<int:batch_id>/", get_email_batch, name="email-batch-detail"),
    path("batches/<int:batch_id>/send/", send_email_batch, name="send-email-batch"),
    path("batches/<int:batch_id>/status/", get_email_batch_status, name="email-batch-status"),
    path("deliveries/<int:delivery_id>/", email_delivery_detail, name="email-delivery-detail"),
    path("deliveries/<int:delivery_id>/resend/", resend_email_delivery, name="resend-email-delivery"),
    path("deliveries/<int:delivery_id>/attachments/upload/", upload_email_attachment, name="upload-email-attachment"),
    path("deliveries/<int:delivery_id>/attachments/existing/", attach_existing_document_to_email, name="attach-existing-document"),
    path("deliveries/<int:delivery_id>/attachments/<int:attachment_id>/", delete_email_attachment, name="delete-email-attachment"),
    path("deliveries/<int:delivery_id>/attachments/<int:attachment_id>/download/", download_email_attachment, name="download-email-attachment"),
]