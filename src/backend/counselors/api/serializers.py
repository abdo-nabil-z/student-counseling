from rest_framework import serializers

from counselors.models import Counselor, AvailabilityBlock

class CounselorCreateSerializer(serializers.ModelSerializer):
    additional_cc = serializers.ListField(child=serializers.EmailField(), required=False)
    chair = serializers.CharField(required=False)

    class Meta:
        model = Counselor
        fields = ["title", "first_name", "last_name", "chair", "office_address", "email", "additional_cc"]

class CounselorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = "__all__"


class AvailabilityBlockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        fields = ["date", "start_time", "end_time"]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError(
                "Start time must be before end time."
            )
        return attrs


class AvailabilityBlockDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        fields = "__all__"