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


class EmailBatchGenerationTests(
    APITestCase
):
    def setUp(self):
        self.url = reverse(
            "mailing_api:create-email-batch"
        )

        # -------------------------------------------------
        # Students
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Counselors
        # -------------------------------------------------

        self.counselor = (
            Counselor.objects.create(
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
        )

        self.counselor_two = (
            Counselor.objects.create(
                title="Dr.",
                first_name="John",
                last_name="Second",
                chair="Institute",
                office_address="AE22-R274",
                email="counselor2@example.com",
                additional_cc=[],
            )
        )

        # -------------------------------------------------
        # Student invitation template
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Appointment invitation template
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Existing counselor preparation template
        # -------------------------------------------------

        Template.objects.update_or_create(
            purpose=(
                Purpose
                .COUNSELOR_PREPARATION_INSTRUCTION_MAIL
            ),
            defaults={
                "content": (
                    "Prepare for "
                    "{{ student.full_name }}."
                )
            },
        )

        # -------------------------------------------------
        # New counselor availability template
        # -------------------------------------------------

        Template.objects.update_or_create(
            purpose=(
                Purpose
                .COUNSELOR_AVAILABILITY_REQUEST_MAIL
            ),
            defaults={
                "content": (
                    "Dear {{ counselor.full_name }}, "
                    "please submit your availability."
                )
            },
        )

        # -------------------------------------------------
        # New counselor appointment summary template
        # -------------------------------------------------

        Template.objects.update_or_create(
            purpose=(
                Purpose
                .COUNSELOR_APPOINTMENTS_SUMMARY_MAIL
            ),
            defaults={
                "content": (
                    "Dear {{ counselor.full_name }}. "
                    "{% for item in appointments %}"
                    "{{ item.student.full_name }}|"
                    "{% endfor %}"
                )
            },
        )

    # =====================================================
    # Student bulk generation
    # =====================================================

    def test_preview_generates_one_draft_per_student(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .STUDENT_INVITATION_MAIL
                ),
                "target_ids": [
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
            first_delivery.status,
            EmailDelivery.Status.DRAFT,
        )

        self.assertEqual(
            second_delivery.status,
            EmailDelivery.Status.DRAFT,
        )

        self.assertEqual(
            first_delivery.recipient_type,
            EmailDelivery
            .RecipientType.STUDENT,
        )

        self.assertEqual(
            second_delivery.recipient_type,
            EmailDelivery
            .RecipientType.STUDENT,
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

    # =====================================================
    # Automatic student generation
    # =====================================================

    def test_send_immediately_creates_queued_deliveries(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .STUDENT_INVITATION_MAIL
                ),
                "target_ids": [
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
                status=(
                    EmailDelivery.Status.QUEUED
                )
            ).count(),
            2,
        )

    # =====================================================
    # Student appointment email
    # =====================================================

    def test_appointment_email_derives_related_objects_from_student(
        self,
    ):
        appointment = (
            Appointment.objects.create(
                student=self.student_one,
                counselor=self.counselor,
                start_time=timezone.now(),
                duration_minutes=30,
                location="AE22-R273",
            )
        )

        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .APPOINTMENT_INVITATION_MAIL
                ),
                "target_ids": [
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

        delivery = (
            EmailDelivery.objects.get()
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery
            .RecipientType.STUDENT,
        )

        self.assertEqual(
            delivery.student_id,
            self.student_one.pk,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

        self.assertEqual(
            delivery.recipient_email,
            self.student_one.email,
        )

        self.assertIn(
            self.counselor.full_name,
            delivery.body,
        )

        expected_start_time = timezone.localtime(
            appointment.start_time
        ).time()

        self.assertIn(
            str(expected_start_time),
            delivery.body,
        )

    # =====================================================
    # Existing counselor preparation email
    #
    # Important:
    # target = student
    # recipient = counselor
    # =====================================================

    def test_counselor_preparation_email_targets_counselor_and_uses_cc(
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
                    Purpose
                    .COUNSELOR_PREPARATION_INSTRUCTION_MAIL
                ),
                "target_ids": [
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

        delivery = (
            EmailDelivery.objects.get()
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery
            .RecipientType.COUNSELOR,
        )

        self.assertEqual(
            delivery.student_id,
            self.student_one.pk,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

        self.assertEqual(
            delivery.recipient_email,
            self.counselor.email,
        )

        self.assertEqual(
            delivery.cc,
            self.counselor.additional_cc,
        )

        self.assertIn(
            self.student_one.full_name,
            delivery.body,
        )

    # =====================================================
    # Counselor bulk availability request
    # =====================================================

    def test_bulk_counselor_availability_email(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .COUNSELOR_AVAILABILITY_REQUEST_MAIL
                ),
                "target_ids": [
                    self.counselor.pk,
                    self.counselor_two.pk,
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
            EmailDelivery.objects.count(),
            2,
        )

        first_delivery = (
            EmailDelivery.objects.get(
                counselor=self.counselor
            )
        )

        second_delivery = (
            EmailDelivery.objects.get(
                counselor=self.counselor_two
            )
        )

        self.assertEqual(
            first_delivery.recipient_type,
            EmailDelivery
            .RecipientType.COUNSELOR,
        )

        self.assertIsNone(
            first_delivery.student_id
        )

        self.assertEqual(
            first_delivery.counselor_id,
            self.counselor.pk,
        )

        self.assertEqual(
            first_delivery.recipient_email,
            self.counselor.email,
        )

        self.assertEqual(
            first_delivery.cc,
            self.counselor.additional_cc,
        )

        self.assertIn(
            self.counselor.full_name,
            first_delivery.body,
        )

        self.assertEqual(
            second_delivery.recipient_type,
            EmailDelivery
            .RecipientType.COUNSELOR,
        )

        self.assertIsNone(
            second_delivery.student_id
        )

        self.assertEqual(
            second_delivery.counselor_id,
            self.counselor_two.pk,
        )

        self.assertEqual(
            second_delivery.recipient_email,
            self.counselor_two.email,
        )

    # =====================================================
    # Individual counselor email
    #
    # Individual = batch with one target.
    # =====================================================

    def test_individual_counselor_email_is_batch_of_one(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .COUNSELOR_AVAILABILITY_REQUEST_MAIL
                ),
                "target_ids": [
                    self.counselor.pk,
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

        batch = EmailBatch.objects.get()

        self.assertEqual(
            batch.deliveries.count(),
            1,
        )

        delivery = (
            batch.deliveries.get()
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery
            .RecipientType.COUNSELOR,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

        self.assertEqual(
            delivery.recipient_email,
            self.counselor.email,
        )

    # =====================================================
    # Counselor accepted appointments summary
    # =====================================================

    def test_counselor_appointments_summary_email(
        self,
    ):
        Appointment.objects.create(
            student=self.student_one,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            location="AE22-R273",
            status=Appointment.Status.BOOKED,
        )

        Appointment.objects.create(
            student=self.student_two,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            location="AE22-R273",
            status=Appointment.Status.CANCELLED,
        )

        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .COUNSELOR_APPOINTMENTS_SUMMARY_MAIL
                ),
                "target_ids": [
                    self.counselor.pk,
                ],
                "send_immediately": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        delivery = (
            EmailDelivery.objects.get()
        )

        self.assertEqual(
            delivery.recipient_type,
            EmailDelivery
            .RecipientType.COUNSELOR,
        )

        self.assertEqual(
            delivery.counselor_id,
            self.counselor.pk,
        )

        self.assertIsNone(
            delivery.student_id
        )

        self.assertEqual(
            delivery.recipient_email,
            self.counselor.email,
        )

        self.assertIn(
            self.student_one.full_name,
            delivery.body,
        )

        self.assertNotIn(
            self.student_two.full_name,
            delivery.body,
        )

    # =====================================================
    # Missing appointment rollback
    # =====================================================

    def test_missing_appointment_rolls_back_entire_batch(
        self,
    ):
        # Only student_one has an appointment.
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
                    Purpose
                    .APPOINTMENT_INVITATION_MAIL
                ),
                "target_ids": [
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

        # generate_email_batch() is atomic.
        # Therefore the successful first delivery
        # must also be rolled back.
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
            "target_ids",
            error["details"],
        )

    # =====================================================
    # Duplicate target validation
    # =====================================================

    def test_duplicate_target_ids_are_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .STUDENT_INVITATION_MAIL
                ),
                "target_ids": [
                    self.student_one.pk,
                    self.student_one.pk,
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

        error = response.json()["error"]

        self.assertIn(
            "target_ids",
            error["details"],
        )

    # =====================================================
    # Missing target validation
    # =====================================================

    def test_missing_student_target_is_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .STUDENT_INVITATION_MAIL
                ),
                "target_ids": [
                    999999,
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

        error = response.json()["error"]

        self.assertIn(
            "target_ids",
            error["details"],
        )

    def test_missing_counselor_target_is_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose
                    .COUNSELOR_AVAILABILITY_REQUEST_MAIL
                ),
                "target_ids": [
                    999999,
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

        error = response.json()["error"]

        self.assertIn(
            "target_ids",
            error["details"],
        )

    # =====================================================
    # Non-email purpose validation
    # =====================================================

    def test_document_purpose_is_rejected(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "purpose": (
                    Purpose.STUDY_PLAN
                ),
                "target_ids": [
                    self.student_one.pk,
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