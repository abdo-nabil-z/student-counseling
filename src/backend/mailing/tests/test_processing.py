import smtplib
from datetime import timedelta
from unittest.mock import patch

from django.test import (
    TestCase,
    override_settings,
)
from django.utils import timezone

from mailing.models import (
    EmailBatch,
    EmailDelivery,
)
from mailing.services.processing import (
    process_next_queued_delivery,
)
from mailing.services.email_settings import ActiveEmailSettings
from students.models import Student
from templates.models import Purpose


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
    DEFAULT_FROM_EMAIL="sender@uni-rostock.de",
    EMAIL_MAX_SEND_ATTEMPTS=2,
    EMAIL_RETRY_DELAY_SECONDS=60,
)
class EmailQueueProcessingTests(TestCase):
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
        self.student = Student.objects.create(
            matriculation_number="400000001",
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
                subject="Counseling invitation",
                body="Dear Anna.",
                status=(
                    EmailDelivery.Status.QUEUED
                ),
            )
        )

    def test_ready_delivery_is_sent(
        self,
    ):
        processed = (
            process_next_queued_delivery()
        )

        self.assertTrue(processed)

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.SENT,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertIsNotNone(
            self.delivery.sent_at
        )

    def test_temporary_failure_is_scheduled_for_retry(
        self,
    ):
        with patch(
            "mailing.services.sending.EmailMessage.send",
            side_effect=(
                smtplib.SMTPServerDisconnected(
                    "Temporary SMTP failure"
                )
            ),
        ):
            process_next_queued_delivery()

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.QUEUED,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertIsNotNone(
            self.delivery.next_attempt_at
        )

        self.assertIn(
            "Temporary SMTP failure",
            self.delivery.last_error,
        )

    def test_second_temporary_failure_becomes_failed(
        self,
    ):
        self.delivery.attempt_count = 1

        self.delivery.save(
            update_fields=[
                "attempt_count",
            ]
        )

        with patch(
            "mailing.services.sending.EmailMessage.send",
            side_effect=(
                smtplib.SMTPServerDisconnected(
                    "Temporary SMTP failure"
                )
            ),
        ):
            process_next_queued_delivery()

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.FAILED,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            2,
        )

        self.assertIsNone(
            self.delivery.next_attempt_at
        )

    def test_permanent_smtp_failure_is_not_retried(
        self,
    ):
        with patch(
            "mailing.services.sending.EmailMessage.send",
            side_effect=smtplib.SMTPDataError(
                550,
                b"Permanent failure",
            ),
        ):
            process_next_queued_delivery()

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.FAILED,
        )

        self.assertEqual(
            self.delivery.attempt_count,
            1,
        )

        self.assertIsNone(
            self.delivery.next_attempt_at
        )

    def test_future_retry_is_not_processed(
        self,
    ):
        self.delivery.next_attempt_at = (
            timezone.now()
            + timedelta(minutes=5)
        )

        self.delivery.save(
            update_fields=[
                "next_attempt_at",
            ]
        )

        processed = (
            process_next_queued_delivery()
        )

        self.assertFalse(processed)

        self.delivery.refresh_from_db()

        self.assertEqual(
            self.delivery.attempt_count,
            0,
        )

        self.assertEqual(
            self.delivery.status,
            EmailDelivery.Status.QUEUED,
        )