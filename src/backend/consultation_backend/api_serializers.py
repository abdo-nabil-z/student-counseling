from rest_framework import serializers


class _APIErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Machine-readable error indetifier.")
    message = serializers.CharField(help_text="Human-readable error description.")
    details = serializers.JSONField(allow_null=True, help_text="Addition error information or field validation errors.")
    request_id = serializers.CharField(help_text="Request identifier used to locate the related backend logs.")


class APIErrorResponseSerializer(serializers.Serializer):
    error = _APIErrorDetailSerializer()
