from rest_framework import serializers

from mailing.models import EmailBatch, EmailDelivery
from students.models import Student
from templates.models import Purpose



EMAIL_PURPOSE_CHOICES = [
    (
        Purpose.STUDENT_INVITATION_MAIL,
        Purpose.STUDENT_INVITATION_MAIL.label,
    ),
    (
        Purpose.STUDENT_REMINDER_MAIL,
        Purpose.STUDENT_REMINDER_MAIL.label,
    ),
    (
        Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL,
        Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL.label,
    ),
    (
        Purpose.APPOINTMENT_INVITATION_MAIL,
        Purpose.APPOINTMENT_INVITATION_MAIL.label,
    ),
    (
        Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL,
        Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL.label,
    ),
    (
        Purpose.APPOINTMENT_CANCELLATION_MAIL,
        Purpose.APPOINTMENT_CANCELLATION_MAIL.label,
    ),
]


class EmailBatchCreateSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=EMAIL_PURPOSE_CHOICES)

    student_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    send_immediately = serializers.BooleanField(default=False, help_text=("If false, generated emails are drafts. ""If true, they are queued for sending."))


    def validate_student_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate student IDs are not allowed.")

        existing_ids = set(
            Student.objects.filter(pk__in=value).values_list("pk", flat=True)
        )

        missing_ids = [
            student_id
            for student_id in value
            if student_id not in existing_ids
        ]

        if missing_ids:
            raise serializers.ValidationError(
                (
                    "The Following students do no exists: "
                    + ", ".join(str(student_id) for student_id in missing_ids)
                )
            )

        return value


class EmailDeliveryPreviewSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = EmailDelivery
        fields = [
            "id",
            "student_id",
            "student_name",
            "recipient_email",
            "cc",
            "subject",
            "body",
            "status",
            "created_at"
        ]

class EmailBatchDetailSerializer(serializers.ModelSerializer):
    deliveries = EmailDeliveryPreviewSerializer(many=True, read_only=True)

    class Meta:
        model = EmailBatch
        fields = [
            "id",
            "purpose",
            "created_at",
            "deliveries"
        ]