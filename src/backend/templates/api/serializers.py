from rest_framework import serializers

from templates.models import Template

from appointments.models import Appointment
from counselors.models import Counselor
from students.models import Student

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ["purpose", "content", "updated_at"]
        read_only_fields = ["purpose", "updated_at"]


# ── Render request serializers (one per input shape) ────────────────────────

class CounselorRenderSerializer(serializers.Serializer):
    counselor_id = serializers.IntegerField(help_text="Counselor ID")

    def validate_counselor_id(self, value):
        if not Counselor.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "A counselor with this ID does not exist."
            )
        
        return value

class StudentRenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="Student ID")

    def validate_student_id(self, value):
        if not Student.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "A student with this ID does not exist."
            )
        
        return value


class StudentCounselorRenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="Student ID")
    counselor_id = serializers.IntegerField(help_text="Counselor ID")
    appointment_id = serializers.IntegerField(help_text="Appointment ID")

    def validate(self, attrs):
        errors = {}

        student_id = attrs["student_id"]
        counselor_id = attrs["counselor_id"]
        appointment_id = attrs["appointment_id"]

        if not Student.objects.filter(pk=student_id).exists():
            errors["student_id"] = [
                "A student with this ID does not exist."
            ]

        if not Counselor.objects.filter(pk=counselor_id).exists():
            errors["counselor_id"] = [
                "A counselor with this ID does not exist."
            ]

        appointment = Appointment.objects.filter(
            pk=appointment_id
        ).first()

        if appointment is None:
            errors["appointment_id"] = [
                "An appointment with this ID does not exist."
            ]
        else:
            if appointment.student_id != student_id:
                errors["student_id"] = [
                    "This student does not belong to the appointment."
                ]

            if appointment.counselor_id != counselor_id:
                errors["counselor_id"] = [
                    "This counselor does not belong to the appointment."
                ]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs