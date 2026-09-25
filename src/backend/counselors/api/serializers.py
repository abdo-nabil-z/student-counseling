from rest_framework import serializers

from counselors.models import Counselor, Slot
from counselors.api_exceptions import SlotOverlapWarning

class CounselorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = [
            "title",
            "first_name",
            "last_name",
            "chair",
            "office_address",
            "email",
            "additional_cc",
        ]


class CounselorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = [
            "title",
            "first_name",
            "last_name",
            "chair",
            "office_address",
            "email",
            "additional_cc",
        ]


class CounselorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = "__all__"


class SlotCreateSerializer(serializers.ModelSerializer):
    allow_overlap = serializers.BooleanField(
    write_only=True,
    default=False,
)
    class Meta:
        model = Slot
        fields = ["date", "start_time", "end_time", "allow_overlap"]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError(
                "Start time must be before end time."
            )

        counselor = self.context.get("counselor")
        allow_overlap = attrs.pop("allow_overlap", False)

        if counselor:
            overlapping_slots = list(
                Slot.objects.filter(
                    counselor=counselor,
                    date=attrs["date"],
                    start_time__lt=attrs["end_time"],
                    end_time__gt=attrs["start_time"],
                ).values(
                    "id",
                    "date",
                    "start_time",
                    "end_time",
                )
            )

            if overlapping_slots and not allow_overlap:
                raise SlotOverlapWarning(details={
                    "overlapping_slots": overlapping_slots,
                    "can_override": True,
                    "override_field": "allow_overlap",
                })

        return attrs


class SlotDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = "__all__"



class SlotStatusStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    matriculation_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField()


class SlotStatusAppointmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    start_time = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()
    end_time = serializers.DateTimeField()
    location = serializers.CharField(allow_null=True)
    student = SlotStatusStudentSerializer()


class SlotStatusSegmentSerializer(serializers.Serializer):
    status = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    appointment = SlotStatusAppointmentSerializer(allow_null=True)


class SlotStatusSlotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    segments = SlotStatusSegmentSerializer(many=True)


class SlotStatusCounselorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    office_address = serializers.CharField()


class CounselorSlotStatusSerializer(serializers.Serializer):
    counselor = SlotStatusCounselorSerializer()
    slots = SlotStatusSlotSerializer(many=True)
    uncovered_appointments = SlotStatusAppointmentSerializer(many=True)
    