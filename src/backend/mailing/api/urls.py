from django.urls import path

from mailing.api.views import create_email_batch


app_name = "mailing_api"


urlpatterns = [
    path("batches/", create_email_batch, name="create-email-batch")
]