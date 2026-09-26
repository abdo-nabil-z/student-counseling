from datetime import datetime
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework.test import APITestCase

from templates.models import Template, Purpose
from appointments.models import Appointment
from counselors.models import Counselor, Slot
from counselors.template_context import (
    AllAvailableSlotsContext,
    CounselorContext,
)
from students.models import Student

class TemplateAPIErrorTests(APITestCase):
    def test_unknown_template_purpose_uses_error_contract(self):
        response = self.client.get(
            "/api/templates/not-a-real-purpose/"
        )

        self.assertEqual(response.status_code, 404)

        error = response.json()["error"]

        self.assertEqual(error["code"], "unknown_template_purpose")
        self.assertIsNone(error["details"])

    
    def test_missing_render_fields_return_validation_error(self):
        Template.objects.create(
            purpose=Purpose.APPOINTMENT_INVITATION_MAIL,
            content="Test template",
        )

        response = self.client.post(
            "/api/templates/appointment_invitation/render/",
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("student_id", error["details"])
        self.assertIn("counselor_id", error["details"])
        self.assertIn("appointment_id", error["details"])

class CounselorMailTemplateTests(
    APITestCase
):
    def setUp(self):
        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Maria",
            last_name="Example",
            chair="Institute",
            office_address="AE22-R273",
            email="maria@example.com",
        )

    def test_availability_request_can_render(
        self,
    ):
        Template.objects.create(
            purpose=(
                Purpose
                .COUNSELOR_AVAILABILITY_REQUEST_MAIL
            ),
            content=(
                "Dear {{ counselor.full_name }}"
            ),
        )

        response = self.client.post(
            (
                "/api/templates/"
                "counselor_availability_request/"
                "render/"
            ),
            data={
                "counselor_id": (
                    self.counselor.pk
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            self.counselor.full_name,
            response.data["rendered"],
        )

    def test_appointments_summary_contains_only_booked(
        self,
    ):
        booked_student = Student.objects.create(
            matriculation_number="900000001",
            first_name="Anna",
            last_name="Booked",
            email="anna@example.com",
        )

        cancelled_student = Student.objects.create(
            matriculation_number="900000002",
            first_name="Peter",
            last_name="Cancelled",
            email="peter@example.com",
        )

        Appointment.objects.create(
            student=booked_student,
            counselor=self.counselor,
            start_time=timezone.now(),
            status=Appointment.Status.BOOKED,
        )

        Appointment.objects.create(
            student=cancelled_student,
            counselor=self.counselor,
            start_time=timezone.now(),
            status=(
                Appointment.Status.CANCELLED
            ),
        )

        Template.objects.create(
            purpose=(
                Purpose
                .COUNSELOR_APPOINTMENTS_SUMMARY_MAIL
            ),
            content=(
                "{% for item in appointments %}"
                "{{ item.student.full_name }}|"
                "{% endfor %}"
            ),
        )

        response = self.client.post(
            (
                "/api/templates/"
                "counselor_appointments_summary/"
                "render/"
            ),
            data={
                "counselor_id": (
                    self.counselor.pk
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        rendered = response.data["rendered"]

        self.assertIn(
            booked_student.full_name,
            rendered,
        )

        self.assertNotIn(
            cancelled_student.full_name,
            rendered,
        )



class TemplateAvailabilityContextTests(APITestCase):
    def setUp(self):
        self.berlin = ZoneInfo("Europe/Berlin")

        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Template",
            last_name="Counselor",
            chair="Institute",
            office_address="Room 1",
            email="template.counselor@example.com",
        )

        self.student = Student.objects.create(
            matriculation_number="600000001",
            first_name="Template",
            last_name="Student",
            email="template.student@example.com",
        )

        self.slot = Slot.objects.create(
            counselor=self.counselor,
            date="2026-09-28",
            start_time="15:00",
            end_time="16:00",
        )

    def test_counselor_context_returns_remaining_free_part_of_slot(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                15,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        context = CounselorContext.from_model(
            self.counselor
        )

        self.assertEqual(
            len(context.slots),
            1,
        )

        free_slot = context.slots[0]

        self.assertEqual(
            free_slot.start_time.strftime("%H:%M"),
            "15:30",
        )

        self.assertEqual(
            free_slot.end_time.strftime("%H:%M"),
            "16:00",
        )

    def test_cancelled_appointment_does_not_reduce_template_availability(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                15,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.CANCELLED,
        )

        context = CounselorContext.from_model(
            self.counselor
        )

        self.assertEqual(
            len(context.slots),
            1,
        )

        free_slot = context.slots[0]

        self.assertEqual(
            free_slot.start_time.strftime("%H:%M"),
            "15:00",
        )

        self.assertEqual(
            free_slot.end_time.strftime("%H:%M"),
            "16:00",
        )

    def test_all_available_slots_context_uses_partial_free_segments(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                15,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        context = AllAvailableSlotsContext.build()

        self.assertEqual(
            len(context.slots),
            1,
        )

        free_slot = context.slots[0]

        self.assertEqual(
            free_slot.start_time.strftime("%H:%M"),
            "15:30",
        )

        self.assertEqual(
            free_slot.end_time.strftime("%H:%M"),
            "16:00",
        )

    def test_appointment_without_slot_still_reduces_template_availability(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=None,
            start_time=datetime(
                2026,
                9,
                28,
                15,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        context = CounselorContext.from_model(
            self.counselor
        )

        self.assertEqual(
            len(context.slots),
            1,
        )

        self.assertEqual(
            context.slots[0].start_time.strftime("%H:%M"),
            "15:30",
        )

        self.assertEqual(
            context.slots[0].end_time.strftime("%H:%M"),
            "16:00",
        )