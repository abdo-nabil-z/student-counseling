from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from appointments.models import Appointment
from counselors.models import Counselor
from mailing.models import (
    EmailBatch,
    EmailDelivery,
)
from students.models import Student
from templates.models import (
    Purpose,
    Template,
)


class EmailBatchGenerationTests(APITestCase):
    def setUp(self):
        self.url = reverse(
            "mailing_api:create-email-batch"
        )

        self.student_one = Student.objects.create(
            matriculation_number="100000001",
            first_name="Anna",
            last_name="Example",
            email="anna@example.com",
            course_of_studies="Computer Science",
            current_study_semester=3,
            credit_points=80,
        )

        self.student_two = Student.objects.create(
            matriculation_number="100000002",
            first_name="Peter",
            last_name="Example",
            email="peter@example.com",
            course_of_studies="Computer Science",
            current_study_semester=4,
            credit_points=100,
        )

        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Maria",
            last_name="Counselor",
            chair="Institute",
            office_address="AE22-R273",
            email="counselor@example.com",
            additional_cc=[
                "secretary@example.com",
            ],
        )

        Template.objects.update_or_create(
            purpose=(
                Purpose.STUDENT_INVITATION_MAIL
            ),
            defaults={
                "content": (
                    "Dear {{ student.first_name }}, "
                    "welcome to counseling."
                )
            },
        )

        Template.objects.update_or_create(
            purpose=(
                Purpose.APPOINTMENT_INVITATION_MAIL
            ),
            defaults={
                "content": (
                    "Dear {{ student.first_name }}, "
                    "your appointment with "
                    "{{ counselor.full_name }} "
                    "starts at "
                    "{{ appointment.start_time }}."
                )
            },
        )

        Template.objects.update_or_create(
            purpose=(
                Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL
            ),
            defaults={
                "content": (
                    "Prepare for "
                    "{{ student.full_name }}."
                )
            },
        )

    def test_preview_generates_one_draft_per_student(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.STUDENT_INVITATION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                    self.student_two.pk,
                ],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            EmailBatch.objects.count(),
            1,
        )

        self.assertEqual(
            EmailDelivery.objects.count(),
            2,
        )

        deliveries = EmailDelivery.objects.order_by(
            "student_id"
        )

        self.assertTrue(
            all(
                delivery.status
                == EmailDelivery.Status.DRAFT
                for delivery in deliveries
            )
        )

        first_delivery = (
            EmailDelivery.objects.get(
                student=self.student_one
            )
        )

        second_delivery = (
            EmailDelivery.objects.get(
                student=self.student_two
            )
        )

        self.assertEqual(
            first_delivery.recipient_email,
            self.student_one.email,
        )

        self.assertEqual(
            second_delivery.recipient_email,
            self.student_two.email,
        )

        self.assertIn(
            "Dear Anna",
            first_delivery.body,
        )

        self.assertIn(
            "Dear Peter",
            second_delivery.body,
        )

    def test_send_immediately_creates_queued_deliveries(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.STUDENT_INVITATION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                    self.student_two.pk,
                ],
                "send_immediately": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            EmailDelivery.objects.filter(
                status=EmailDelivery.Status.QUEUED
            ).count(),
            2,
        )

    def test_appointment_email_derives_related_objects_from_student(
        self,
    ):
        appointment = Appointment.objects.create(
            student=self.student_one,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            location="AE22-R273",
        )

        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.APPOINTMENT_INVITATION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                ],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        delivery = EmailDelivery.objects.get()

        self.assertEqual(
            delivery.student_id,
            self.student_one.pk,
        )

        self.assertEqual(
            delivery.recipient_email,
            self.student_one.email,
        )

        self.assertIn(
            self.counselor.full_name,
            delivery.body,
        )

        self.assertIn(
            str(
                appointment.start_time.time()
            ),
            delivery.body,
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery.RecipientType.STUDENT,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

    def test_counselor_email_targets_counselor_and_uses_cc(
        self,
    ):
        Appointment.objects.create(
            student=self.student_one,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            location="AE22-R273",
        )

        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                ],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        delivery = EmailDelivery.objects.get()

        self.assertEqual(
            delivery.recipient_email,
            self.counselor.email,
        )

        self.assertEqual(
            delivery.cc,
            self.counselor.additional_cc,
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery.RecipientType.COUNSELOR,
        )

        self.assertEqual(
            delivery.student_id,
            self.student_one.pk,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

    def test_missing_appointment_rolls_back_entire_batch(
        self,
    ):
        Appointment.objects.create(
            student=self.student_one,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
        )

        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.APPOINTMENT_INVITATION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                    self.student_two.pk,
                ],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            EmailBatch.objects.count(),
            0,
        )

        self.assertEqual(
            EmailDelivery.objects.count(),
            0,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "validation_error",
        )

        self.assertIn(
            "student_ids",
            error["details"],
        )

    def test_duplicate_student_ids_are_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.STUDENT_INVITATION_MAIL
                ),
                "student_ids": [
                    self.student_one.pk,
                    self.student_one.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            EmailBatch.objects.count(),
            0,
        )

    def test_document_purpose_is_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": Purpose.STUDY_PLAN,
                "student_ids": [
                    self.student_one.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            EmailBatch.objects.count(),
            0,
        )