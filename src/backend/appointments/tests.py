from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.models import Appointment
from appointments.appointment_context import AppointmentContext
from counselors.models import Counselor, Slot
from documents.models import Document
from students.models import Student


class AppointmentAPIErrorTests(APITestCase):
    def test_invalid_student_filter_returns_validation_error(self):
        response = self.client.get(
            "/api/appointments/?student=not-an-integer"
        )

        self.assertEqual(response.status_code, 400)
        
        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("student", error["details"])


class AppointmentDocumentCascadeDeleteTests(TestCase):
    def setUp(self):
        super().setUp()

        self.media_directory = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()

        self.counselor = Counselor.objects.create(
            title="Dr.",
            first_name="Test",
            last_name="Counselor",
            chair="Institute",
            office_address="AE22-R273",
            email="counselor@example.com",
        )

        self.student = Student.objects.create(
            matriculation_number="123456789",
            first_name="Test",
            last_name="Student",
            email="student@example.com",
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()

        return super().tearDown()

    def test_deleting_appointment_deletes_minutes_document_and_file(self):
        appointment_minutes = Document.objects.create(
            file=SimpleUploadedFile(name="direct-appointment-minutes.rtf", content=b"Test document content"),
            name="Appointment minutes",
        )

        appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            minutes=appointment_minutes,
        )

        appointment_id = appointment.pk
        document_id = appointment_minutes.pk
        file_path = Path(appointment_minutes.file.path).resolve()

        self.assertTrue(file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            appointment.delete()

        self.assertFalse(Appointment.objects.filter(pk=appointment_id).exists())
        self.assertFalse(Document.objects.filter(pk=document_id).exists())
        self.assertFalse(file_path.exists())
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists())
        self.assertTrue(Counselor.objects.filter(pk=self.counselor.pk).exists())


class AppointmentSchedulingRuleTests(APITestCase):
    def setUp(self):
        self.counselor_one = Counselor.objects.create(
            title="Prof.",
            first_name="Anna",
            last_name="One",
            chair="Institute",
            office_address="Room 1",
            email="counselor1@example.com",
        )

        self.counselor_two = Counselor.objects.create(
            title="Prof.",
            first_name="Bob",
            last_name="Two",
            chair="Institute",
            office_address="Room 2",
            email="counselor2@example.com",
        )

        self.student_one = self.create_student(
            "100000001",
            "student1@example.com",
        )

        self.student_two = self.create_student(
            "100000002",
            "student2@example.com",
        )

        self.student_three = self.create_student(
            "100000003",
            "student3@example.com",
        )

        self.berlin = ZoneInfo("Europe/Berlin")

    def create_student(self, matriculation_number, email):
        return Student.objects.create(
            matriculation_number=matriculation_number,
            first_name="Test",
            last_name=matriculation_number,
            email=email,
        )

    def create_existing_appointment(
        self,
        *,
        student,
        counselor,
        hour=10,
        minute=0,
        status=Appointment.Status.BOOKED,
    ):
        return Appointment.objects.create(
            student=student,
            counselor=counselor,
            start_time=datetime(
                2026,
                9,
                28,
                hour,
                minute,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=status,
        )

    def test_same_counselor_overlapping_appointment_returns_warning(self):
        self.create_existing_appointment(
            student=self.student_one,
            counselor=self.counselor_one,
        )

        response = self.client.post(
            "/api/appointments/create-appointment/",
            {
                "student": self.student_two.pk,
                "counselor": self.counselor_one.pk,
                "slot": None,
                "start_time": "2026-09-28T10:15:00+02:00",
                "duration_minutes": 30,
                "location": "Room 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "appointment_overlap_warning",
        )

        self.assertTrue(
            error["details"]["can_override"]
        )

        self.assertEqual(
            error["details"]["override_field"],
            "allow_overlap",
        )

        self.assertEqual(
            len(
                error["details"][
                    "overlapping_appointments"
                ]
            ),
            1,
        )


class AppointmentTimezoneTests(TestCase):
    def setUp(self):
        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Timezone",
            last_name="Test",
            chair="Institute",
            office_address="Room 1",
            email="timezone@example.com",
        )

        self.student = Student.objects.create(
            matriculation_number="400000001",
            first_name="Time",
            last_name="Student",
            email="time.student@example.com",
        )

    def test_project_uses_berlin_timezone(self):
        self.assertEqual(
            settings.TIME_ZONE,
            "Europe/Berlin",
        )

    def test_appointment_context_converts_utc_to_berlin_time(self):
        appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=datetime(
                2026,
                9,
                26,
                13,
                30,
                tzinfo=ZoneInfo("UTC"),
            ),
            duration_minutes=30,
        )

        context = AppointmentContext.from_model(
            appointment
        )

        self.assertEqual(
            context.start_time.hour,
            15,
        )

        self.assertEqual(
            context.start_time.minute,
            30,
        )

        self.assertEqual(
            context.end_time.hour,
            16,
        )