from django.contrib import admin
from documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "uploaded_at"]
    readonly_fields = ["uploaded_at"]
