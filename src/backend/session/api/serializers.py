from rest_framework import serializers

from session.models import CounselingSession
from counselors.api.serializers import CounselorDetailSerializer, AppointmentSlotSerializer
from students.api.serializers import StudentDetailSerializer


# Used when CREATING a session (client sends just the IDs)
class CounselingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounselingSession
        fields = ["student", "counselor", "slot"]


# Used when LISTING sessions (expands the related records for display)
class CounselingSessionDetailSerializer(serializers.ModelSerializer):
    student = StudentDetailSerializer(read_only=True)
    counselor = CounselorDetailSerializer(read_only=True)
    slot = AppointmentSlotSerializer(read_only=True)

    class Meta:
        model = CounselingSession
        fields = ["id", "student", "counselor", "slot", "status",
                  "notes", "initial_study_plan", "final_study_plan",
                  "created_at", "updated_at"]