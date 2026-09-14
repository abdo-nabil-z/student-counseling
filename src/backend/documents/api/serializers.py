from django.urls import reverse
from rest_framework import serializers

from documents.models import Document


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Display name. Defaults to the uploaded filename.",
    )


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
