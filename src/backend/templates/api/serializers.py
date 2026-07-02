from rest_framework import serializers

from templates.models import Template


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ["purpose", "content", "updated_at"]
        read_only_fields = ["purpose", "updated_at"]


# ── Render request serializers (one per input shape) ────────────────────────

class CounselorRenderSerializer(serializers.Serializer):
    counselor_id = serializers.IntegerField(help_text="Counselor ID")


class StudentRenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="Student ID")


class StudentCounselorRenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="Student ID")
    counselor_id = serializers.IntegerField(help_text="Counselor ID")
