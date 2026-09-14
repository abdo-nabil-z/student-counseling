from unittest.mock import patch

from django.core import mail
from django.test import (
    TestCase,
    override_settings,
)

from mailing.models import (
    EmailBatch,
    EmailDelivery,
)
from mailing.services.sending import (
    EmailDeliverySendError,
    EmailDeliveryStateError,
    send_email_delivery_once,
)
from students.models import Student
from templates.models import Purpose


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
    DEFAULT_FROM_EMAIL="sender@uni-rostock.de",
)
class EmailSendingServiceTests(TestCase):
    def setUp(self):
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
            "sender@uni-rostock.de",
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