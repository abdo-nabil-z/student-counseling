from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.models import Appointment
from counselors.models import Counselor
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
