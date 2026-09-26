from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from appointments.models import Appointment
from appointments.api_exceptions import AppointmentOverlapWarning
from counselors.api.serializers import CounselorDetailSerializer, SlotDetailSerializer
from students.api.serializers import StudentDetailSerializer
from documents.api.serializers import DocumentInfoSerializer


ACTIVE_APPOINTMENT_STATUSES = (
    Appointment.Status.PENDING,
    Appointment.Status.BOOKED,
)


def _slot_bounds(slot):
    current_timezone = timezone.get_current_timezone()

    slot_start = timezone.make_aware(
        datetime.combine(slot.date, slot.start_time),
        current_timezone,
    )

    slot_end = timezone.make_aware(
        datetime.combine(slot.date, slot.end_time),
        current_timezone,
    )

    return slot_start, slot_end


def _validate_slot_relation(
    *,
    counselor,
    slot,
    start_time,
    duration_minutes,
):
    if slot is None:
        return

    if slot.counselor_id != counselor.pk:
        raise serializers.ValidationError({
            "slot": [
                "The selected availability slot belongs to "
                "a different counselor."
            ]
        })

    appointment_start = timezone.localtime(start_time)
    appointment_end = appointment_start + timedelta(
        minutes=duration_minutes
    )

    slot_start, slot_end = _slot_bounds(slot)

    if appointment_start < slot_start or appointment_end > slot_end:
        raise serializers.ValidationError({
            "slot": [
                "The appointment does not fit inside the "
                "selected availability slot. Use slot=null "
                "for an appointment outside availability."
            ]
        })


def _find_overlapping_appointments(
    *,
    counselor,
    start_time,
    duration_minutes,
    exclude_appointment_id=None,
):
    end_time = start_time + timedelta(
        minutes=duration_minutes
    )

    appointments = (
        Appointment.objects
        .filter(
            counselor=counselor,
            status__in=ACTIVE_APPOINTMENT_STATUSES,
            start_time__lt=end_time,
        )
        .select_related("student")
    )

    if exclude_appointment_id is not None:
        appointments = appointments.exclude(
            pk=exclude_appointment_id
        )

    overlapping = []

    for appointment in appointments:
        appointment_end = (
            appointment.start_time
            + timedelta(
                minutes=appointment.duration_minutes
            )
        )

        if appointment_end <= start_time:
            continue

        local_start = timezone.localtime(
            appointment.start_time
        )

        local_end = local_start + timedelta(
            minutes=appointment.duration_minutes
        )

        overlapping.append({
            "id": appointment.pk,
            "student_id": appointment.student_id,
            "student_name": appointment.student.full_name,
            "status": appointment.status,
            "start_time": local_start.isoformat(),
            "end_time": local_end.isoformat(),
        })

    return overlapping


def _check_appointment_overlap(
    *,
    counselor,
    start_time,
    duration_minutes,
    allow_overlap,
    exclude_appointment_id=None,
):
    if allow_overlap:
        return

    overlapping = _find_overlapping_appointments(
        counselor=counselor,
        start_time=start_time,
        duration_minutes=duration_minutes,
        exclude_appointment_id=exclude_appointment_id,
    )

    if overlapping:
        raise AppointmentOverlapWarning(
            details={
                "overlapping_appointments": overlapping,
                "can_override": True,
                "override_field": "allow_overlap",
            }
        )


# Used when CREATING a session
class AppointmentSerializer(serializers.ModelSerializer):
    allow_overlap = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )

    class Meta:
        model = Appointment
        fields = [
            "student",
            "counselor",
            "slot",
            "start_time",
            "duration_minutes",
            "location",
            "allow_overlap",
        ]

    def validate(self, attrs):
        allow_overlap = attrs.pop(
            "allow_overlap",
            False,
        )

        counselor = attrs["counselor"]
        slot = attrs.get("slot")
        start_time = attrs["start_time"]
        duration_minutes = attrs["duration_minutes"]

        _validate_slot_relation(
            counselor=counselor,
            slot=slot,
            start_time=start_time,
            duration_minutes=duration_minutes,
        )

        _check_appointment_overlap(
            counselor=counselor,
            start_time=start_time,
            duration_minutes=duration_minutes,
            allow_overlap=allow_overlap,
        )

        return attrs


# Used when LISTING appointments (expands the related records for display)
class AppointmentDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    student = StudentDetailSerializer(read_only=True)
    counselor = CounselorDetailSerializer(read_only=True)
    slot = SlotDetailSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    minutes = DocumentInfoSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = "__all__"


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    allow_overlap = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )

    class Meta:
        model = Appointment
        fields = [
            "counselor",
            "slot",
            "start_time",
            "duration_minutes",
            "location",
            "status",
            "allow_overlap",
        ]

        extra_kwargs = {
            "counselor": {"required": False},
            "slot": {
                "required": False,
                "allow_null": True,
            },
            "start_time": {"required": False},
            "duration_minutes": {"required": False},
            "location": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "status": {"required": False},
        }

    def validate(self, attrs):
        allow_overlap = attrs.pop(
            "allow_overlap",
            False,
        )

        counselor = attrs.get(
            "counselor",
            self.instance.counselor,
        )

        slot = attrs.get(
            "slot",
            self.instance.slot,
        )

        start_time = attrs.get(
            "start_time",
            self.instance.start_time,
        )

        duration_minutes = attrs.get(
            "duration_minutes",
            self.instance.duration_minutes,
        )

        appointment_status = attrs.get(
            "status",
            self.instance.status,
        )

        slot_related_fields = {
            "counselor",
            "slot",
            "start_time",
            "duration_minutes",
        }

        if any(
            field in attrs
            for field in slot_related_fields
        ):
            _validate_slot_relation(
                counselor=counselor,
                slot=slot,
                start_time=start_time,
                duration_minutes=duration_minutes,
            )

        overlap_related_fields = {
            "counselor",
            "start_time",
            "duration_minutes",
            "status",
        }

        if (
            appointment_status
            in ACTIVE_APPOINTMENT_STATUSES
            and any(
                field in attrs
                for field in overlap_related_fields
            )
        ):
            _check_appointment_overlap(
                counselor=counselor,
                start_time=start_time,
                duration_minutes=duration_minutes,
                allow_overlap=allow_overlap,
                exclude_appointment_id=self.instance.pk,
            )

        return attrs


class AppointmentFilterSerializer(serializers.Serializer):
    
    student = serializers.IntegerField(required=False, min_value=1, help_text="Filter by student ID.")
    counselor = serializers.IntegerField(required=False, min_value=1, help_text="Filter by counselor ID.")