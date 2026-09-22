import tempfile

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from counselors.models import Counselor
from documents.models import Document
from documents.services import attach_document
from mailing.models import (
    EmailAttachment,
    EmailBatch,
    EmailDelivery,
)
from students.models import Student
from templates.models import Purpose, Template
from appointments.models import Appointment


class EmailAttachmentTests(APITestCase):
    def setUp(self):
        self.media_directory = (
            tempfile.TemporaryDirectory()
        )

        self.settings_override = (
            override_settings(
                MEDIA_ROOT=(
                    self.media_directory.name
                )
            )
        )

        self.settings_override.enable()

        self.student = Student.objects.create(
            matriculation_number="100000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
        )

        self.counselor = (
            Counselor.objects.create(
                title="Prof.",
                first_name="Maria",
                last_name="Counselor",
                chair="Institute",
                office_address="AE22-R273",
                email="prof@example.com",
                additional_cc=[],
            )
        )

        self.batch = EmailBatch.objects.create(
            purpose=(
                Purpose
                .STUDENT_INVITATION_MAIL
            )
        )

        self.delivery = (
            EmailDelivery.objects.create(
                batch=self.batch,
                recipient_type=(
                    EmailDelivery
                    .RecipientType.STUDENT
                ),
                student=self.student,
                recipient_email=(
                    self.student.email
                ),
                cc=[],
                subject="Test",
                body="Test body",
                status=(
                    EmailDelivery.Status.DRAFT
                ),
            )
        )

        self.initial_document = (
            attach_document(
                file=SimpleUploadedFile(
                    "initial-plan.pdf",
                    b"original study plan",
                    content_type=(
                        "application/pdf"
                    ),
                ),
                name="Initial Study Plan",
            )
        )

        self.student.initial_study_plan = (
            self.initial_document
        )

        self.student.save(
            update_fields=[
                "initial_study_plan"
            ]
        )

        Template.objects.update_or_create(
            purpose=Purpose.STUDY_PLAN,
            defaults={
                "content": (
                    "# Study Plan\n\n"
                    "Student: "
                    "{{ student.full_name }}"
                )
            },
        )

        Template.objects.update_or_create(
            purpose=Purpose.STUDENT_INVITATION_MAIL,
            defaults={
                "content": "Dear {{ student.first_name }}, this is a test invitation."
            },
        )

        Template.objects.update_or_create(
            purpose=Purpose.STUDY_PLAN,
            defaults={
                "content": "# Study Plan\n\nStudent: {{ student.full_name }}"
            },
        )

        Template.objects.update_or_create(
            purpose=(
                Purpose.APPOINTMENT_MINUTES
            ),
            defaults={
                "content": (
                    "# Appointment Minutes\n\n"
                    "Student: "
                    "{{ student.full_name }}\n\n"
                    "Counselor: "
                    "{{ counselor.full_name }}"
                )
            },
        )


    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_upload_arbitrary_file(
        self,
    ):
        url = reverse(
            (
                "mailing_api:"
                "upload-email-attachment"
            ),
            args=[self.delivery.pk],
        )

        file = SimpleUploadedFile(
            "notes.txt",
            b"hello from device",
            content_type="text/plain",
        )

        response = self.client.post(
            url,
            data={
                "file": file,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        attachment = (
            EmailAttachment.objects.get()
        )

        self.assertEqual(
            attachment.source,
            EmailAttachment.Source.UPLOADED,
        )

        self.assertIsNone(
            attachment.source_document_id
        )

        self.assertEqual(
            attachment.name,
            "notes.txt",
        )

        self.assertEqual(
            attachment.content_type,
            "text/plain",
        )

        attachment.file.open("rb")

        try:
            self.assertEqual(
                attachment.file.read(),
                b"hello from device",
            )

        finally:
            attachment.file.close()

    def test_existing_document_is_copied_as_snapshot(
        self,
    ):
        url = reverse(
            (
                "mailing_api:"
                "attach-existing-document"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "document_id": (
                    self.initial_document.pk
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        attachment = (
            EmailAttachment.objects.get()
        )

        self.assertEqual(
            attachment.source,
            EmailAttachment.Source.EXISTING,
        )

        self.assertEqual(
            attachment.source_document_id,
            self.initial_document.pk,
        )

        self.assertNotEqual(
            attachment.file.name,
            self.initial_document.file.name,
        )

        self.initial_document.file.open(
            "rb"
        )

        attachment.file.open("rb")

        try:
            original_bytes = (
                self.initial_document
                .file
                .read()
            )

            attachment_bytes = (
                attachment.file.read()
            )

        finally:
            self.initial_document.file.close()
            attachment.file.close()

        self.assertEqual(
            attachment_bytes,
            original_bytes,
        )

    def test_unrelated_document_is_rejected(
        self,
    ):
        unrelated_document = (
            attach_document(
                file=SimpleUploadedFile(
                    "other.pdf",
                    b"other student document",
                    content_type=(
                        "application/pdf"
                    ),
                ),
                name="Other Document",
            )
        )

        url = reverse(
            (
                "mailing_api:"
                "attach-existing-document"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "document_id": (
                    unrelated_document.pk
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            EmailAttachment.objects.count(),
            0,
        )

    def test_same_existing_document_cannot_be_added_twice(
        self,
    ):
        url = reverse(
            (
                "mailing_api:"
                "attach-existing-document"
            ),
            args=[self.delivery.pk],
        )

        payload = {
            "document_id": (
                self.initial_document.pk
            )
        }

        first_response = self.client.post(
            url,
            data=payload,
            format="json",
        )

        second_response = self.client.post(
            url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            EmailAttachment.objects.count(),
            1,
        )

    def test_email_preview_contains_attachments(
        self,
    ):
        upload_url = reverse(
            (
                "mailing_api:"
                "upload-email-attachment"
            ),
            args=[self.delivery.pk],
        )

        self.client.post(
            upload_url,
            data={
                "file": SimpleUploadedFile(
                    "notes.txt",
                    b"hello",
                    content_type="text/plain",
                ),
            },
            format="multipart",
        )

        detail_url = reverse(
            (
                "mailing_api:"
                "email-delivery-detail"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.get(
            detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(
                response.data[
                    "attachments"
                ]
            ),
            1,
        )

        self.assertEqual(
            response.data[
                "attachments"
            ][0]["name"],
            "notes.txt",
        )

    def test_attachment_can_be_downloaded(
        self,
    ):
        upload_url = reverse(
            (
                "mailing_api:"
                "upload-email-attachment"
            ),
            args=[self.delivery.pk],
        )

        upload_response = (
            self.client.post(
                upload_url,
                data={
                    "file": (
                        SimpleUploadedFile(
                            "notes.txt",
                            b"download me",
                            content_type=(
                                "text/plain"
                            ),
                        )
                    ),
                },
                format="multipart",
            )
        )

        attachment_id = (
            upload_response.data["id"]
        )

        download_url = reverse(
            (
                "mailing_api:"
                "download-email-attachment"
            ),
            args=[
                self.delivery.pk,
                attachment_id,
            ],
        )

        response = self.client.get(
            download_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        content = b"".join(
            response.streaming_content
        )

        self.assertEqual(
            content,
            b"download me",
        )

    def test_deleting_attachment_keeps_original_document(
        self,
    ):
        create_url = reverse(
            (
                "mailing_api:"
                "attach-existing-document"
            ),
            args=[self.delivery.pk],
        )

        create_response = (
            self.client.post(
                create_url,
                data={
                    "document_id": (
                        self.initial_document.pk
                    )
                },
                format="json",
            )
        )

        attachment = (
            EmailAttachment.objects.get(
                pk=create_response.data["id"]
            )
        )

        attachment_storage = (
            attachment.file.storage
        )

        attachment_file_name = (
            attachment.file.name
        )

        original_file_name = (
            self.initial_document.file.name
        )

        delete_url = reverse(
            (
                "mailing_api:"
                "delete-email-attachment"
            ),
            args=[
                self.delivery.pk,
                attachment.pk,
            ],
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            response = self.client.delete(
                delete_url
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            EmailAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )

        self.assertTrue(
            Document.objects.filter(
                pk=self.initial_document.pk
            ).exists()
        )

        self.assertTrue(
            self.initial_document
            .file
            .storage
            .exists(
                original_file_name
            )
        )

        self.assertFalse(
            attachment_storage.exists(
                attachment_file_name
            )
        )

    def test_queued_email_cannot_receive_attachment(
        self,
    ):
        self.delivery.status = (
            EmailDelivery.Status.QUEUED
        )

        self.delivery.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        url = reverse(
            (
                "mailing_api:"
                "upload-email-attachment"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "file": SimpleUploadedFile(
                    "notes.txt",
                    b"hello",
                ),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        self.assertEqual(
            EmailAttachment.objects.count(),
            0,
        )

    def test_counselor_preparation_email_can_attach_students_plan(
        self,
    ):
        batch = EmailBatch.objects.create(
            purpose=(
                Purpose
                .COUNSELOR_PREPARATION_INSTRUCTION_MAIL
            )
        )

        delivery = (
            EmailDelivery.objects.create(
                batch=batch,
                recipient_type=(
                    EmailDelivery
                    .RecipientType.COUNSELOR
                ),
                student=self.student,
                counselor=self.counselor,
                recipient_email=(
                    self.counselor.email
                ),
                cc=[],
                subject="Prepare",
                body="Prepare for student",
                status=(
                    EmailDelivery.Status.DRAFT
                ),
            )
        )

        url = reverse(
            (
                "mailing_api:"
                "attach-existing-document"
            ),
            args=[delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "document_id": (
                    self.initial_document.pk
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        attachment = (
            EmailAttachment.objects.get(
                delivery=delivery
            )
        )

        self.assertEqual(
            attachment.source_document_id,
            self.initial_document.pk,
        )


    def test_generated_pdf_returns_document_id(
        self,
    ):
        url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "purpose": (
                    Purpose.STUDY_PLAN
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            set(response.data.keys()),
            {
                "document_id",
            },
        )

        document_id = (
            response.data["document_id"]
        )

        self.assertTrue(
            Document.objects.filter(
                pk=document_id
            ).exists()
        )

        attachment = (
            EmailAttachment.objects.get(
                delivery=self.delivery
            )
        )

        self.assertEqual(
            attachment.source,
            EmailAttachment.Source.GENERATED,
        )

        self.assertEqual(
            attachment.source_document_id,
            document_id,
        )

        self.assertFalse(
            bool(attachment.file)
        )

        self.assertEqual(
            attachment.content_type,
            "application/pdf",
        )



    def test_generated_document_contains_pdf(
        self,
    ):
        url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "purpose": (
                    Purpose.STUDY_PLAN
                )
            },
            format="json",
        )

        document = Document.objects.get(
            pk=response.data["document_id"]
        )

        document.file.open("rb")

        try:
            content = document.file.read()

        finally:
            document.file.close()

        self.assertTrue(
            content.startswith(
                b"%PDF"
            )
        )


    def test_generated_pdf_can_be_downloaded_through_documents_api(
        self,
    ):
        generate_url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        generate_response = (
            self.client.post(
                generate_url,
                data={
                    "purpose": (
                        Purpose.STUDY_PLAN
                    )
                },
                format="json",
            )
        )

        document_id = (
            generate_response.data[
                "document_id"
            ]
        )

        download_url = reverse(
            "documents_api:download",
            args=[document_id],
        )

        response = self.client.get(
            download_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        content = b"".join(
            response.streaming_content
        )

        self.assertTrue(
            content.startswith(
                b"%PDF"
            )
        )


    def test_generated_pdf_and_uploaded_file_can_coexist(
        self,
    ):
        upload_url = reverse(
            (
                "mailing_api:"
                "upload-email-attachment"
            ),
            args=[self.delivery.pk],
        )

        upload_response = (
            self.client.post(
                upload_url,
                data={
                    "file": (
                        SimpleUploadedFile(
                            "notes.txt",
                            b"Professor notes",
                            content_type=(
                                "text/plain"
                            ),
                        )
                    )
                },
                format="multipart",
            )
        )

        self.assertEqual(
            upload_response.status_code,
            status.HTTP_201_CREATED,
        )

        generated_url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        generated_response = (
            self.client.post(
                generated_url,
                data={
                    "purpose": (
                        Purpose.STUDY_PLAN
                    )
                },
                format="json",
            )
        )

        self.assertEqual(
            generated_response.status_code,
            status.HTTP_201_CREATED,
        )

        attachments = (
            EmailAttachment.objects.filter(
                delivery=self.delivery
            )
        )

        self.assertEqual(
            attachments.count(),
            2,
        )

        self.assertTrue(
            attachments.filter(
                source=(
                    EmailAttachment
                    .Source
                    .UPLOADED
                )
            ).exists()
        )

        self.assertTrue(
            attachments.filter(
                source=(
                    EmailAttachment
                    .Source
                    .GENERATED
                )
            ).exists()
        )


    def test_appointment_minutes_pdf_can_be_generated(
        self,
    ):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            location="AE22-R273",
        )

        url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            url,
            data={
                "purpose": (
                    Purpose.APPOINTMENT_MINUTES
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        document = Document.objects.get(
            pk=response.data["document_id"]
        )

        self.assertTrue(
            bool(document.file)
        )


    def test_deleting_generated_attachment_deletes_generated_document(
        self,
    ):
        generate_url = reverse(
            (
                "mailing_api:"
                "generate-email-pdf-attachment"
            ),
            args=[self.delivery.pk],
        )

        response = self.client.post(
            generate_url,
            data={
                "purpose": (
                    Purpose.STUDY_PLAN
                )
            },
            format="json",
        )

        document_id = (
            response.data["document_id"]
        )

        attachment = (
            EmailAttachment.objects.get(
                delivery=self.delivery,
                source=(
                    EmailAttachment
                    .Source
                    .GENERATED
                ),
            )
        )

        delete_url = reverse(
            (
                "mailing_api:"
                "delete-email-attachment"
            ),
            args=[
                self.delivery.pk,
                attachment.pk,
            ],
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            delete_response = (
                self.client.delete(
                    delete_url
                )
            )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Document.objects.filter(
                pk=document_id
            ).exists()
        )


    def test_batch_can_still_be_created_without_attachments(self):
        response = self.client.post(
            reverse("mailing_api:create-email-batch"),
            {
                "purpose": Purpose.STUDENT_INVITATION_MAIL,
                "target_ids": [self.student.pk],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["deliveries"][0]["attachments"], [])


    def test_batch_creation_can_generate_pdf_attachment(self):
        response = self.client.post(
            reverse("mailing_api:create-email-batch"),
            {
                "purpose": Purpose.STUDENT_INVITATION_MAIL,
                "target_ids": [self.student.pk],
                "send_immediately": False,
                "generated_pdf_purposes": [Purpose.STUDY_PLAN],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        attachment = response.data["deliveries"][0]["attachments"][0]

        self.assertEqual(attachment["source"], EmailAttachment.Source.GENERATED)
        self.assertIsNotNone(attachment["document_id"])
        self.assertTrue(Document.objects.filter(pk=attachment["document_id"]).exists())


    def test_batch_creation_supports_uploaded_and_generated_attachments(self):
        response = self.client.post(
            reverse("mailing_api:create-email-batch"),
            {
                "purpose": Purpose.STUDENT_INVITATION_MAIL,
                "target_ids": [self.student.pk],
                "send_immediately": False,
                "generated_pdf_purposes": [Purpose.STUDY_PLAN],
                "uploaded_files": [
                    SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
                ],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        attachments = response.data["deliveries"][0]["attachments"]
        self.assertEqual(len(attachments), 2)
        self.assertEqual({item["source"] for item in attachments}, {
            EmailAttachment.Source.GENERATED,
            EmailAttachment.Source.UPLOADED,
        })


    def test_batch_creation_can_attach_initial_study_plan(self):
        response = self.client.post(
            reverse("mailing_api:create-email-batch"),
            {
                "purpose": Purpose.STUDENT_INVITATION_MAIL,
                "target_ids": [self.student.pk],
                "send_immediately": False,
                "existing_document_types": ["initial_study_plan"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["deliveries"][0]["attachments"][0]["source"],
            EmailAttachment.Source.EXISTING,
        )


    def test_batch_creation_can_attach_multiple_generated_pdf_templates(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
        )

        response = self.client.post(
            reverse("mailing_api:create-email-batch"),
            {
                "purpose": Purpose.STUDENT_INVITATION_MAIL,
                "target_ids": [self.student.pk],
                "send_immediately": False,
                "generated_pdf_purposes": [
                    Purpose.STUDY_PLAN,
                    Purpose.APPOINTMENT_MINUTES,
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        attachments = response.data["deliveries"][0]["attachments"]

        self.assertEqual(len(attachments), 2)

        self.assertTrue(
            all(
                attachment["source"] == EmailAttachment.Source.GENERATED
                for attachment in attachments
            )
        )

        document_ids = [attachment["document_id"] for attachment in attachments]

        self.assertEqual(len(set(document_ids)), 2)

        for document_id in document_ids:
            self.assertTrue(Document.objects.filter(pk=document_id).exists())

        attachment_names = {attachment["name"] for attachment in attachments}

        self.assertEqual(
            attachment_names,
            {
                f"study-plan-{self.student.pk}.pdf",
                f"appointment-minutes-{self.student.pk}.pdf",
            },
        )
            