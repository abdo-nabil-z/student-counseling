from django.urls import reverse
from rest_framework import serializers

from mailing.models import EmailBatch, EmailDelivery, EmailAttachment
from mailing.purpose_config import EMAIL_PURPOSE_CHOICES, EMAIL_PURPOSE_CONFIG
from students.models import Student
from templates.models import Purpose
from counselors.models import Counselor



class EmailBatchCreateSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=EMAIL_PURPOSE_CHOICES)

    target_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False,
                                        help_text=(
                                            "IDs of the entities selected for this email purpose. "
                                            "Student purposes expect student IDs; "
                                            "counselor purposes expect counselor IDs."
                                        ),)

    send_immediately = serializers.BooleanField(default=False, help_text=("If false, generated emails are drafts. If true, they are queued for sending."))


    def validate_target_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate target IDs are not allowed.")

        return value

    
    def validate(self, attrs):
        purpose = attrs["purpose"]
        target_ids = attrs["target_ids"]

        config = EMAIL_PURPOSE_CONFIG[purpose]

        if config.target_type == "student":
            model = Student
            target_label = "students"
        else:
            model = Counselor
            target_label="counselor"

        existing_ids = set(
            model.objects.filter(pk__in=target_ids).values_list("pk", flat=True)
        )

        missing_ids = [
            target_id
            for target_id in target_ids
            if target_id not in existing_ids
        ]

        if missing_ids:
            raise serializers.ValidationError(
                {
                    "target_ids": [
                        (
                            f"The following {target_label} do not exist: "
                            + ", ".join(
                                str(target_id)
                                for target_id
                                in missing_ids
                            )
                        )
                    ]
                }
            )

        return attrs


class EmailAttachmentSerializer(serializers.ModelSerializer):
    source_document_id = (
        serializers.IntegerField(
            read_only=True,
            allow_null=True,
        )
    )

    download_url = (
        serializers.SerializerMethodField()
    )

    document_id = serializers.SerializerMethodField()

    class Meta:
        model = EmailAttachment

        fields = [
            "id",
            "source",
            "source_document_id",
            "document_id",
            "name",
            "content_type",
            "download_url",
            "created_at",
        ]

    def get_download_url(
        self,
        obj,
    ):
        if obj.source == EmailAttachment.Source.GENERATED:
            return None
        return reverse(
            (
                "mailing_api:"
                "download-email-attachment"
            ),
            args=[
                obj.delivery_id,
                obj.pk,
            ],
        )

    def get_document_id(self, obj):
        if(obj.source == EmailAttachment.Source.GENERATED):
            return obj.source_document_id

        return None


class EmailAttachmentUploadSerializer(
    serializers.Serializer
):
    file = serializers.FileField()

    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text=(
            "Display name. Defaults to the "
            "uploaded filename."
        ),
    )


class ExistingEmailAttachmentSerializer(
    serializers.Serializer
):
    document_id = serializers.IntegerField(
        min_value=1,
    )


class EmailDeliveryPreviewSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(read_only=True, allow_null=True)
    student_name = serializers.SerializerMethodField()

    counselor_id = serializers.IntegerField(read_only=True, allow_null=True)
    counselor_name = serializers.SerializerMethodField()

    attachments = EmailAttachmentSerializer(
    many=True,
    read_only=True,
)

    def get_student_name(self, obj):
        if obj.student is None:
            return None

        return obj.student.full_name

    def get_counselor_name(self, obj):
        if obj.counselor is None:
            return None

        return obj.counselor.full_name

    class Meta:
        model = EmailDelivery

        fields = [
            "id",
            "recipient_type",
            "student_id",
            "student_name",
            "counselor_id",
            "counselor_name",
            "recipient_email",
            "cc",
            "subject",
            "body",
            "status",
            "attachments",
            "created_at",
        ]


class GeneratedEmailAttachmentSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=[
        (
            Purpose.STUDY_PLAN,
            Purpose.STUDY_PLAN.label,
        ),
        (
            Purpose.APPOINTMENT_MINUTES,
            Purpose.APPOINTMENT_MINUTES.label,
        )
    ])

    name = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Optional PDF name. The .pdf extension is added automatically.")


class GeneratedEmailAttachmentResponseSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()


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
    student_id = serializers.IntegerField(read_only=True, allow_null=True)

    counselor_id = serializers.IntegerField(read_only=True, allow_null=True)

    student_name = serializers.SerializerMethodField()

    counselor_name = serializers.SerializerMethodField()

    def get_student_name(self, obj):
        if obj.student is None:
            return None

        return obj.student.full_name

    def get_counselor_name( self, obj):
        if obj.counselor is None:
            return None

        return obj.counselor.full_name

    class Meta:
        model = EmailDelivery

        fields = [
            "id",
            "recipient_type",
            "student_id",
            "student_name",
            "counselor_id",
            "counselor_name",
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