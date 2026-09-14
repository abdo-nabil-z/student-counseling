from django.urls import path
from documents.api import views

app_name = "documents_api"

urlpatterns = [
    # Entity-bound documents
    path("<int:pk>/", views.delete_document, name="delete"),
    path("<int:pk>/download/", views.download_document, name="download"),
]
