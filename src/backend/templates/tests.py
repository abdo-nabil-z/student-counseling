from django.utils import timezone
from rest_framework.test import APITestCase

from templates.models import Template, Purpose
from appointments.models import Appointment
from counselors.models import Counselor
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