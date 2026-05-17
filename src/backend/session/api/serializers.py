from rest_framework import serializers

from session.models import CounselingSession

class CounselingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounselingSession
        fields = ["student", "counselor", "slot"]
        