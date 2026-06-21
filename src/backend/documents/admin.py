from django.contrib import admin
from documents.models import Document, MasterDocument, MasterDocumentVersion


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


@admin.register(MasterDocument)
class MasterDocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(MasterDocumentVersion)
class MasterDocumentVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "master", "created_at"]
    readonly_fields = ["created_at"]
