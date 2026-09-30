import tempfile
from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from documents.models import Document
from documents.services import attach_document
from mailing.models import EmailAttachment, EmailBatch, EmailDelivery
from mailing.services.sending import (
    EmailDeliverySendError,
    EmailDeliveryStateError,
    send_email_delivery_once,
)
from students.models import Student
from templates.models import Purpose
from mailing.services.email_settings import ActiveEmailSettings


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
    DEFAULT_FROM_EMAIL="sender@uni-rostock.de",
)
class EmailSendingServiceTests(TestCase):
    def setUp(self):
        self.email_settings_patcher = patch(
            "mailing.services.sending.get_active_email_settings",
            return_value=ActiveEmailSettings(
                smtp_host="smtp.test.local",
                smtp_port=587,
                use_tls=True,
                smtp_username="test-user",
                password="test-password",
                from_name="Prof. Test",
                from_email="sender@uni-rostock.de",
                persist_credentials=False,
            ),
        )

        self.email_settings_patcher.start()
        self.addCleanup(
            self.email_settings_patcher.stop
        )
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        
        self.student = Student.objects.create(
            matriculation_number="300000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
        )

        self.batch = EmailBatch.objects.create(
            purpose=(
                Purpose.STUDENT_INVITATION_MAIL
            )
        )

        self.delivery = (
            EmailDelivery.objects.create(
                batch=self.batch,
                student=self.student,
                recipient_email=(
                    self.student.email
                ),
                cc=[
                    "copy@example.com",
                ],
                subject="Counseling invitation",
                body="Dear Anna, welcome.",
                status=(
                    EmailDelivery.Status.QUEUED
                ),
            )
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()
        super().tearDown()


    def test_queued_delivery_is_sent_successfully(
        self,
    ):
        send_email_delivery_once(
            self.delivery
        )

        self.delivery.refresh_from_db()

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        sent_email = mail.outbox[0]

        self.assertEqual(
            sent_email.subject,
            "Counseling invitation",
        )

        self.assertEqual(
            sent_email.body,
            "Dear Anna, welcome.",
        )

        self.assertEqual(
            sent_email.from_email,
            '"Prof. Test" <sender@uni-rostock.de>',
        )

        self.assertEqual(
            sent_email.reply_to,
            ["sender@uni-rostock.de"],
        )

        self.assertEqual(
            sent_email.extra_headers["X-Mailer"],
            "Study Counseling System",
        )

        self.assertEqual(
            sent_email.to,
            [
                "anna@example.com",
            ],
        )

        self.assertEqual(
            sent_email.cc,
            [
                "copy@example.com",
            ],
        )

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.SENT,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertEqual(
            self.delivery.last_error,
            "",
        )

        self.assertIsNotNone(
            self.delivery.sent_at
        )

        self.student.refresh_from_db()

        self.assertEqual(
            self.student.contact_status,
            Student.ContactStatus.EMAILED,
        )

    def test_send_failure_is_recorded_and_reraised(
        self,
    ):
        with patch(
            "mailing.services.sending.EmailMessage.send",
            side_effect=OSError(
                "Simulated SMTP failure"
            ),
        ):
            with self.assertLogs(
                "mailing.services.sending",
                level="WARNING",
            ):
                with self.assertRaises(
                    OSError
                ):
                    send_email_delivery_once(
                        self.delivery
                    )

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.QUEUED,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertEqual(
            self.delivery.last_error,
            "Simulated SMTP failure",
        )

        self.assertIsNone(
            self.delivery.sent_at
        )

        self.student.refresh_from_db()

        self.assertEqual(
            self.student.contact_status,
            Student.ContactStatus.NOT_CONTACTED_YET,
        )

    def test_non_queued_delivery_cannot_be_sent(
        self,
    ):
        self.delivery.status = (
            EmailDelivery.Status.DRAFT
        )

        self.delivery.save(
            update_fields=[
                "status",
            ]
        )

        with self.assertRaises(
            EmailDeliveryStateError
        ):
            send_email_delivery_once(
                self.delivery
            )

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.attempt_count,
            0,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_backend_zero_result_is_treated_as_failure(
        self,
    ):
        with patch(
            "mailing.services.sending.EmailMessage.send",
            return_value=0,
        ):
            with self.assertLogs(
                "mailing.services.sending",
                level="WARNING",
            ):
                with self.assertRaises(
                    EmailDeliverySendError
                ):
                    send_email_delivery_once(
                        self.delivery
                    )

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.QUEUED,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertIn(
            "did not confirm",
            self.delivery.last_error,
        )


    def test_uploaded_attachment_is_sent_and_cleaned(self):
        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.UPLOADED,
            name="notes.txt",
            content_type="text/plain",
        )

        attachment.file.save(
            "notes.txt",
            SimpleUploadedFile(
                "notes.txt",
                b"Professor notes",
                content_type="text/plain",
            ),
        )

        storage = attachment.file.storage
        stored_name = attachment.file.name

        self.assertTrue(storage.exists(stored_name))

        send_email_delivery_once(self.delivery)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].attachments), 1)

        sent_attachment = mail.outbox[0].attachments[0]

        self.assertEqual(sent_attachment[0], "notes.txt")
        self.assertEqual(sent_attachment[1], "Professor notes")
        self.assertEqual(sent_attachment[2], "text/plain")

        attachment.refresh_from_db()

        self.assertFalse(storage.exists(stored_name))
        self.assertFalse(bool(attachment.file))
        self.assertIsNotNone(attachment.cleaned_at)
        self.assertEqual(attachment.cleanup_error, "")



    def test_generated_pdf_is_sent_and_cleaned(self):
        document = attach_document(
            file=SimpleUploadedFile(
                "generated.pdf",
                b"%PDF-1.4 generated test",
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
        )

        send_email_delivery_once(self.delivery)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].attachments), 1)

        sent_attachment = mail.outbox[0].attachments[0]

        self.assertEqual(sent_attachment[0], "generated.pdf")
        self.assertEqual(sent_attachment[1], b"%PDF-1.4 generated test")
        self.assertEqual(sent_attachment[2], "application/pdf")

        attachment.refresh_from_db()

        self.assertFalse(Document.objects.filter(pk=document_id).exists())
        self.assertFalse(storage.exists(stored_name))
        self.assertIsNone(attachment.source_document_id)
        self.assertIsNotNone(attachment.cleaned_at)
        self.assertEqual(attachment.cleanup_error, "")


    def test_existing_document_original_survives_send(self):
        original_document = attach_document(
            file=SimpleUploadedFile(
                "initial-plan.pdf",
                b"Student original plan",
                content_type="application/pdf",
            ),
            name="Initial Study Plan",
        )

        original_id = original_document.pk
        original_storage = original_document.file.storage
        original_name = original_document.file.name

        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.EXISTING,
            source_document=original_document,
            name="Initial Study Plan",
            content_type="application/pdf",
        )

        attachment.file.save(
            "initial-plan.pdf",
            SimpleUploadedFile(
                "initial-plan.pdf",
                b"Student original plan",
                content_type="application/pdf",
            ),
        )

        snapshot_storage = attachment.file.storage
        snapshot_name = attachment.file.name

        send_email_delivery_once(self.delivery)

        attachment.refresh_from_db()

        self.assertTrue(Document.objects.filter(pk=original_id).exists())
        self.assertTrue(original_storage.exists(original_name))

        self.assertFalse(snapshot_storage.exists(snapshot_name))
        self.assertFalse(bool(attachment.file))

        self.assertEqual(attachment.source_document_id, original_id)
        self.assertIsNotNone(attachment.cleaned_at)


    def test_uploaded_and_generated_attachments_are_sent_together(self):
        uploaded = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.UPLOADED,
            name="notes.txt",
            content_type="text/plain",
        )

        uploaded.file.save(
            "notes.txt",
            SimpleUploadedFile(
                "notes.txt",
                b"Professor notes",
                content_type="text/plain",
            ),
        )

        document = attach_document(
            file=SimpleUploadedFile(
                "study-plan.pdf",
                b"%PDF-1.4 study plan",
                content_type="application/pdf",
            ),
            name="Study Plan",
        )

        EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.GENERATED,
            source_document=document,
            name="study-plan.pdf",
            content_type="application/pdf",
        )

        send_email_delivery_once(self.delivery)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].attachments), 2)

        attachment_names = {
            item[0]
            for item in mail.outbox[0].attachments
        }

        self.assertEqual(
            attachment_names,
            {"notes.txt", "study-plan.pdf"},
        )



    def test_send_failure_keeps_generated_attachment(self):
        document = attach_document(
            file=SimpleUploadedFile(
                "generated.pdf",
                b"%PDF-1.4 retry test",
                content_type="application/pdf",
            ),
            name="Generated PDF",
        )

        document_id = document.pk
        stored_name = document.file.name
        storage = document.file.storage

        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.GENERATED,
            source_document=document,
            name="generated.pdf",
            content_type="application/pdf",
        )

        with patch(
            "mailing.services.sending.EmailMessage.send",
            side_effect=OSError("SMTP unavailable"),
        ):
            with self.assertLogs("mailing.services.sending", level="WARNING"):
                with self.assertRaises(OSError):
                    send_email_delivery_once(self.delivery)

        attachment.refresh_from_db()
        self.delivery.refresh_from_db()

        self.assertEqual(self.delivery.status, EmailDelivery.Status.QUEUED)
        self.assertTrue(Document.objects.filter(pk=document_id).exists())
        self.assertTrue(storage.exists(stored_name))
        self.assertEqual(attachment.source_document_id, document_id)
        self.assertIsNone(attachment.cleaned_at)


    def test_cleanup_failure_does_not_make_sent_email_fail(self):
        document = attach_document(
            file=SimpleUploadedFile(
                "generated.pdf",
                b"%PDF-1.4 cleanup test",
                content_type="application/pdf",
            ),
            name="Generated PDF",
        )

        attachment = EmailAttachment.objects.create(
            delivery=self.delivery,
            source=EmailAttachment.Source.GENERATED,
            source_document=document,
            name="generated.pdf",
            content_type="application/pdf",
        )

        with patch(
            "mailing.services.sending._cleanup_generated_document",
            side_effect=OSError("Delete failed"),
        ):
            with self.assertLogs("mailing.services.sending", level="ERROR"):
                send_email_delivery_once(self.delivery)

        self.delivery.refresh_from_db()
        attachment.refresh_from_db()

        self.assertEqual(self.delivery.status, EmailDelivery.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)

        self.assertIsNone(attachment.cleaned_at)
        self.assertIn("Delete failed", attachment.cleanup_error)

        self.assertTrue(
            Document.objects.filter(pk=document.pk).exists()
        )   


    def test_successful_email_does_not_downgrade_confirmed_student(self):
        self.student.contact_status = Student.ContactStatus.CONFIRMED
        self.student.save(update_fields=["contact_status"])

        send_email_delivery_once(self.delivery)

        self.student.refresh_from_db()

        self.assertEqual(
            self.student.contact_status,
            Student.ContactStatus.CONFIRMED,
        )