from rest_framework import serializers

from appointments.models import Appointment
from counselors.api.serializers import CounselorDetailSerializer, SlotDetailSerializer
from students.api.serializers import StudentDetailSerializer
from documents.api.serializers import DocumentInfoSerializer


# Used when CREATING a session
class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["student", "counselor", "slot", "start_time", "end_time", "location"]


# Used when LISTING appointments (expands the related records for display)
class AppointmentDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())
    counselor = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())
    slot = SlotDetailSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    minutes = DocumentInfoSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "student", "counselor", "slot", "start_time", "end_time", "status",
            "location", "minutes",
            "created_at", "updated_at",
        ]