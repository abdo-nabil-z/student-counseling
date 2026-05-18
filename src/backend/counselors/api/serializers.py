from rest_framework import serializers

from counselors.models import Counselor, AvailabilitySlot

class CounselorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = ["first_name", "last_name", "user_id", "department"]



class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ["counselor", "start_time"]