from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from mailing.models import (
    EmailBatch,
    EmailDelivery,
)
from students.models import Student
from templates.models import Purpose


class EmailPreviewAPITests(APITestCase):
    def setUp(self):
        self.student_one = Student.objects.create(
            matriculation_number="200000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
        )

        self.student_two = Student.objects.create(
            matriculation_number="200000002",
            first_name="Peter",
            last_name="Example",
            email="peter@example.com",
        )

        self.batch = EmailBatch.objects.create(
            purpose=(
                Purpose.STUDENT_INVITATION_MAIL
            )
        )

        self.delivery_one = (
            EmailDelivery.objects.create(
                batch=self.batch,
                student=self.student_one,
                recipient_email=(
                    self.student_one.email
                ),
                subject="Original subject",
                body="Original body for Anna",
                status=(
                    EmailDelivery.Status.DRAFT
                ),
            )
        )

        self.delivery_two = (
            EmailDelivery.objects.create(
                batch=self.batch,
                student=self.student_two,
                recipient_email=(
                    self.student_two.email
                ),
                subject="Original subject",
                body="Original body for Peter",
                status=(
                    EmailDelivery.Status.DRAFT
                ),
            )
        )

    def test_batch_detail_returns_all_deliveries(
        self,
    ):
        url = reverse(
            "mailing_api:email-batch-detail",
            args=[self.batch.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.batch.pk,
        )

        self.assertEqual(
            len(response.data["deliveries"]),
            2,
        )

    def test_delivery_detail_returns_preview(
        self,
    ):
        url = reverse(
            "mailing_api:email-delivery-detail",
            args=[self.delivery_one.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.delivery_one.pk,
        )

        self.assertEqual(
            response.data["subject"],
            "Original subject",
        )

    def test_draft_email_subject_and_body_can_be_edited(
        self,
    ):
        url = reverse(
            "mailing_api:email-delivery-detail",
            args=[self.delivery_one.pk],
        )

        response = self.client.patch(
            url,
            data={
                "subject": "Edited subject",
                "body": "Edited body",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.delivery_one.refresh_from_db()
        self.delivery_two.refresh_from_db()

        self.assertEqual(
            self.delivery_one.subject,
            "Edited subject",
        )

        self.assertEqual(
            self.delivery_one.body,
            "Edited body",
        )

        self.assertEqual(
            self.delivery_two.subject,
            "Original subject",
        )

        self.assertEqual(
            self.delivery_two.body,
            "Original body for Peter",
        )

    def test_empty_patch_is_rejected(
        self,
    ):
        url = reverse(
            "mailing_api:email-delivery-detail",
            args=[self.delivery_one.pk],
        )

        response = self.client.patch(
            url,
            data={},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "validation_error",
        )

    def test_queued_email_cannot_be_edited(
        self,
    ):
        self.delivery_one.status = (
            EmailDelivery.Status.QUEUED
        )
        self.delivery_one.save(
            update_fields=["status"]
        )

        url = reverse(
            "mailing_api:email-delivery-detail",
            args=[self.delivery_one.pk],
        )

        response = self.client.patch(
            url,
            data={
                "subject": "Should not change",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "email_delivery_not_editable",
        )

        self.delivery_one.refresh_from_db()

        self.assertEqual(
            self.delivery_one.subject,
            "Original subject",
        )

    def test_sending_batch_queues_all_drafts(
        self,
    ):
        url = reverse(
            "mailing_api:send-email-batch",
            args=[self.batch.pk],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.delivery_one.refresh_from_db()
        self.delivery_two.refresh_from_db()

        self.assertEqual(
            self.delivery_one.status,
            EmailDelivery.Status.QUEUED,
        )

        self.assertEqual(
            self.delivery_two.status,
            EmailDelivery.Status.QUEUED,
        )

    def test_already_queued_batch_cannot_be_sent_again(
        self,
    ):
        EmailDelivery.objects.filter(
            batch=self.batch
        ).update(
            status=EmailDelivery.Status.QUEUED
        )

        url = reverse(
            "mailing_api:send-email-batch",
            args=[self.batch.pk],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "email_batch_not_sendable",
        )

    def test_missing_batch_returns_404(
        self,
    ):
        url = reverse(
            "mailing_api:email-batch-detail",
            args=[999999],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_batch_list_returns_saved_batches_newest_first(self):
        newer_batch = EmailBatch.objects.create(
            purpose=Purpose.STUDENT_REMINDER_MAIL
        )

        EmailDelivery.objects.create(
            batch=newer_batch,
            recipient_type=EmailDelivery.RecipientType.STUDENT,
            student=self.student_one,
            recipient_email=self.student_one.email,
            subject="Newer subject",
            body="Newer body",
            status=EmailDelivery.Status.QUEUED,
        )

        url = reverse("mailing_api:create-email-batch")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]["id"], newer_batch.pk)
        self.assertEqual(response.data[1]["id"], self.batch.pk)


    def test_batch_list_contains_delivery_information(self):
        self.delivery_one.last_error = "Previous SMTP failure"
        self.delivery_one.save(update_fields=["last_error"])

        url = reverse("mailing_api:create-email-batch")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        batch = response.data[0]
        delivery = batch["deliveries"][0]

        self.assertEqual(batch["recipient_type"], "student")

        self.assertEqual(delivery["student"], self.student_one.pk)
        self.assertIsNone(delivery["counselor"])

        self.assertEqual(delivery["recipient_email"], self.student_one.email)
        self.assertEqual(delivery["recipient_name"], self.student_one.full_name)

        self.assertEqual(delivery["subject"], "Original subject")
        self.assertEqual(delivery["body"], "Original body for Anna")
        self.assertEqual(delivery["status"], EmailDelivery.Status.DRAFT)

        self.assertEqual(
            delivery["error_message"],
            "Previous SMTP failure",
        )


    def test_batch_list_does_not_create_batches(self):
        count_before = EmailBatch.objects.count()

        response = self.client.get(
            reverse("mailing_api:create-email-batch")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(EmailBatch.objects.count(), count_before)