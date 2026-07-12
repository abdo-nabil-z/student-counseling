from django.urls import reverse
from rest_framework import serializers

from documents.models import Document, MasterDocument, MasterDocumentVersion


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Display name. Defaults to the uploaded filename.",
    )


class MasterDocumentVersionUploadSerializer(
    serializers.Serializer
):
    file = serializers.FileField()


class DocumentInfoSerializer(serializers.ModelSerializer):
    """Minimal read-only representation embedded in entity serializers."""
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "name", "download_url"]

    def get_download_url(self, obj):
        request = self.context.get("request")
        url = reverse("documents_api:download", args=[obj.id])
        return request.build_absolute_uri(url) if request else url


class MasterDocumentVersionSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = MasterDocumentVersion
        fields = ["id", "created_at", "download_url"]

    def get_download_url(self, obj):
        request = self.context.get("request")
        url = reverse("documents_api:download-master-version", args=[obj.id])
        return request.build_absolute_uri(url) if request else url


class MasterDocumentSerializer(serializers.ModelSerializer):
    versions = MasterDocumentVersionSerializer(many=True, read_only=True)
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = MasterDocument
        fields = ["id", "name", "latest_version", "versions"]

    def get_latest_version(self, obj):
        v = obj.versions.first()
        return MasterDocumentVersionSerializer(v, context=self.context).data if v else None
