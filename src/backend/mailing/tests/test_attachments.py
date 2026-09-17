import tempfile

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import override_settings
from django.urls import reverse

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
from templates.models import Purpose


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