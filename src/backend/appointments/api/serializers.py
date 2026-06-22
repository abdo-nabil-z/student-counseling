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
    student = StudentDetailSerializer(read_only=True)
    counselor = CounselorDetailSerializer(read_only=True)
    slot = SlotDetailSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    minutes = DocumentInfoSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = "__all__"