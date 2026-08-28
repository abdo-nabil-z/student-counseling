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


class EmailDeliveryUpdateSerializer(serializers.Serializer):
    subject = serializers.CharField(required=False, allow_blank=False, max_length=255)

    body = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field must be provided.")

        return attrs

    def update(self, instance, validated_data):
        updated_fields = []

        if "subject" in validated_data:
            instance.subject = (
                validated_data["subject"]
            )
            updated_fields.append("subject")

        if "body" in validated_data:
            instance.body = (
                validated_data["body"]
            )
            updated_fields.append("body")

        updated_fields.append("updated_at")

        instance.save(
            update_fields=updated_fields
        )

        return instance

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


class EmailDeliveryStatusSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(read_only=True)

    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True
    )

    class Meta:
        model = EmailDelivery
        fields = [
            "id",
            "student_id",
            "student_name",
            "recipient_email",
            "status",
            "attempt_count",
            "last_error",
            "next_attempt_at",
            "sent_at",
            "updated_at",
        ]


class EmailBatchStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    purpose = serializers.CharField()

    total_count = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    queued_count = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()

    deliveries = EmailDeliveryStatusSerializer(
        many=True
    )