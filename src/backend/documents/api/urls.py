from django.urls import path
from documents.api import views

app_name = "documents_api"

urlpatterns = [
    # Entity-bound documents
    path("<int:pk>/", views.delete_document, name="delete"),
    path("<int:pk>/download/", views.download_document, name="download"),

    # Master documents
    path("master/", views.list_master_documents, name="list-master"),
    path("master/<int:pk>/versions/", views.upload_master_version, name="upload-master-version"),
    path("master/versions/<int:pk>/download/", views.download_master_version, name="download-master-version"),
]
