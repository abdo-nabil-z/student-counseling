import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from documents.models import Document
from documents.services import attach_document
from mailing.models import EmailAttachment, EmailBatch, EmailDelivery
from students.models import Student
from templates.models import Purpose


class EmailAttachmentCleanupTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()

        self.student = Student.objects.create(
            matriculation_number="100000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
        )

        self.batch = EmailBatch.objects.create(
            purpose=Purpose.STUDENT_INVITATION_MAIL
        )

        self.delivery = EmailDelivery.objects.create(
            batch=self.batch,
            recipient_type=EmailDelivery.RecipientType.STUDENT,
            student=self.student,
            recipient_email=self.student.email,
            cc=[],
            subject="Test",
            body="Test body",
            status=EmailDelivery.Status.SENT,
            attempt_count=1,
            sent_at=timezone.now(),
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()
        super().tearDown()


    def test_cleanup_command_removes_uploaded_attachment(self):
        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.UPLOADED,
            name="notes.txt",
            content_type="text/plain",
            cleanup_error="Previous delete failure",
        )

        attachment.file.save(
            "notes.txt",
            SimpleUploadedFile(
                "notes.txt",
                b"Temporary email attachment",
                content_type="text/plain",
            ),
        )

        storage = attachment.file.storage
        stored_name = attachment.file.name

        self.assertTrue(storage.exists(stored_name))

        call_command("cleanup_email_attachments")

        attachment.refresh_from_db()

        self.assertFalse(storage.exists(stored_name))
        self.assertFalse(bool(attachment.file))
        self.assertIsNotNone(attachment.cleaned_at)
        self.assertEqual(attachment.cleanup_error, "")


    def test_cleanup_command_removes_generated_document(self):
        document = attach_document(
            file=SimpleUploadedFile(
                "generated.pdf",
                b"%PDF-1.4 cleanup test",
                content_type="application/pdf",
            ),
            name="Generated PDF",
        )

        document_id = document.pk
        storage = document.file.storage
        stored_name = document.file.name

        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.GENERATED,
            source_document=document,
            name="generated.pdf",
            content_type="application/pdf",
            cleanup_error="Previous delete failure",
        )

        call_command("cleanup_email_attachments")

        attachment.refresh_from_db()

        self.assertFalse(
            Document.objects.filter(pk=document_id).exists()
        )

        self.assertFalse(storage.exists(stored_name))
        self.assertIsNone(attachment.source_document_id)
        self.assertIsNotNone(attachment.cleaned_at)
        self.assertEqual(attachment.cleanup_error, "")


    def test_cleanup_command_does_not_clean_failed_delivery(self):
        self.delivery.status = EmailDelivery.Status.FAILED
        self.delivery.save(update_fields=["status", "updated_at"])

        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.UPLOADED,
            name="retry.txt",
            content_type="text/plain",
        )

        attachment.file.save(
            "retry.txt",
            SimpleUploadedFile(
                "retry.txt",
                b"Needed for resend",
                content_type="text/plain",
            ),
        )

        storage = attachment.file.storage
        stored_name = attachment.file.name

        call_command("cleanup_email_attachments")

        attachment.refresh_from_db()

        self.assertTrue(storage.exists(stored_name))
        self.assertTrue(bool(attachment.file))
        self.assertIsNone(attachment.cleaned_at)