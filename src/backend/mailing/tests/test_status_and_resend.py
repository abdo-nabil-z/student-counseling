from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from mailing.models import (
    EmailBatch,
    EmailDelivery,
)
from students.models import Student
from templates.models import Purpose


class EmailStatusAndResendTests(
    APITestCase
):
    def setUp(self):
        self.student_one = Student.objects.create(
            matriculation_number="500000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
        )

        self.student_two = Student.objects.create(
            matriculation_number="500000002",
            first_name="Peter",
            last_name="Example",
            email="peter@example.com",
        )

        self.batch = EmailBatch.objects.create(
            purpose=(
                Purpose.STUDENT_INVITATION_MAIL
            )
        )

        self.sent_delivery = (
            EmailDelivery.objects.create(
                batch=self.batch,
                student=self.student_one,
                recipient_email=(
                    self.student_one.email
                ),
                subject="Sent subject",
                body="Sent body",
                status=(
                    EmailDelivery.Status.SENT
                ),
                attempt_count=1,
                sent_at=timezone.now(),
            )
        )

        self.failed_delivery = (
            EmailDelivery.objects.create(
                batch=self.batch,
                student=self.student_two,
                recipient_email=(
                    self.student_two.email
                ),
                subject="Failed subject",
                body="Failed body",
                status=(
                    EmailDelivery.Status.FAILED
                ),
                attempt_count=2,
                last_error="Mailbox unavailable",
            )
        )

    def test_batch_status_returns_counts(
        self,
    ):
        url = reverse(
            "mailing_api:email-batch-status",
            args=[self.batch.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_count"],
            2,
        )

        self.assertEqual(
            response.data["sent_count"],
            1,
        )

        self.assertEqual(
            response.data["failed_count"],
            1,
        )

        self.assertEqual(
            response.data["queued_count"],
            0,
        )

        self.assertEqual(
            response.data["draft_count"],
            0,
        )

    def test_status_response_does_not_include_body(
        self,
    ):
        url = reverse(
            "mailing_api:email-batch-status",
            args=[self.batch.pk],
        )

        response = self.client.get(url)

        delivery = response.data[
            "deliveries"
        ][0]

        self.assertNotIn(
            "body",
            delivery,
        )

        self.assertNotIn(
            "subject",
            delivery,
        )

    def test_failed_delivery_can_be_edited(
        self,
    ):
        url = reverse(
            "mailing_api:email-delivery-detail",
            args=[self.failed_delivery.pk],
        )

        response = self.client.patch(
            url,
            data={
                "subject": "Corrected subject",
                "body": "Corrected body",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.failed_delivery.refresh_from_db()

        self.assertEqual(
            self.failed_delivery.subject,
            "Corrected subject",
        )

        self.assertEqual(
            self.failed_delivery.body,
            "Corrected body",
        )

        self.assertEqual(
            self.failed_delivery.status,
            EmailDelivery.Status.FAILED,
        )

    def test_failed_delivery_can_be_requeued(
        self,
    ):
        self.failed_delivery.next_attempt_at = (
            timezone.now()
            + timedelta(minutes=5)
        )

        self.failed_delivery.save(
            update_fields=[
                "next_attempt_at",
            ]
        )

        url = reverse(
            "mailing_api:resend-email-delivery",
            args=[self.failed_delivery.pk],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.failed_delivery.refresh_from_db()

        self.assertEqual(
            self.failed_delivery.status,
            EmailDelivery.Status.QUEUED,
        )

        self.assertEqual(
            self.failed_delivery.attempt_count,
            0,
        )

        self.assertEqual(
            self.failed_delivery.last_error,
            "",
        )

        self.assertIsNone(
            self.failed_delivery.next_attempt_at
        )

    def test_sent_delivery_cannot_be_resent(
        self,
    ):
        url = reverse(
            "mailing_api:resend-email-delivery",
            args=[self.sent_delivery.pk],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "email_delivery_not_resendable",
        )

    def test_missing_delivery_returns_404(
        self,
    ):
        url = reverse(
            "mailing_api:resend-email-delivery",
            args=[999999],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )