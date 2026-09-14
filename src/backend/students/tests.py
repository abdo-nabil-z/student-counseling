from datetime import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.models import Appointment
from counselors.models import Counselor, Slot
from documents.models import Document
from students.models import Student
from students.services.semester_cleanup import delete_semester_data


class StudentAPIErrorTests(APITestCase):
    def test_invalid_semester_cleanup_confirmation_uses_error_contract(self):
        response = self.client.delete(
            "/api/students/semester-cleanup/",
            data={
                "confirm": "wrong-value",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("confirm", error["details"])
        self.assertEqual(error["request_id"], response["X-Request-ID"])


class StudentDocumentCascadeDeleteTests(TestCase):
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

    def create_document(self, file_name: str, display_name: str) -> Document:
        return Document.objects.create(
            file=SimpleUploadedFile(name=file_name, content=b"Test document content"),
            name=display_name,
        )

    def test_deleting_student_deletes_all_attached_documents_and_files(self):
        initial_study_plan = self.create_document("initial-study-plan.docx", "Initial study plan")
        final_study_plan = self.create_document("final-study-plan.xlsx", "Final study plan")
        appointment_minutes = self.create_document("appointment-minutes.txt", "Appointment minutes")

        self.student.initial_study_plan = initial_study_plan
        self.student.final_study_plan = final_study_plan
        self.student.save(update_fields=["initial_study_plan", "final_study_plan"])

        appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            minutes=appointment_minutes,
        )

        student_id = self.student.pk
        appointment_id = appointment.pk
        document_ids = {initial_study_plan.pk, final_study_plan.pk, appointment_minutes.pk}
        file_paths = {
            Path(initial_study_plan.file.path).resolve(),
            Path(final_study_plan.file.path).resolve(),
            Path(appointment_minutes.file.path).resolve(),
        }

        for file_path in file_paths:
            self.assertTrue(file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            self.student.delete()

        self.assertFalse(Student.objects.filter(pk=student_id).exists())
        self.assertFalse(Appointment.objects.filter(pk=appointment_id).exists())
        self.assertTrue(Counselor.objects.filter(pk=self.counselor.pk).exists())
        self.assertFalse(Document.objects.filter(pk__in=document_ids).exists())

        for file_path in file_paths:
            self.assertFalse(file_path.exists())



class SemesterCleanupServiceTests(TestCase):
    def setUp(self):
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

        self.slot = Slot.objects.create(
            counselor=self.counselor,
            date=timezone.localdate(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        self.appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=timezone.now(),
            duration_minutes=30,
        )


    def test_cleanup_deletes_semester_data_and_keeps_counselor(self):
        result = delete_semester_data()

        self.assertEqual(
            result,
            {
                "deleted_appointments": 1,
                "deleted_students": 1,
                "deleted_slots": 1,
            },
        )

        self.assertEqual(Appointment.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Slot.objects.count(), 0)

        self.assertTrue(
            Counselor.objects.filter(pk=self.counselor.pk).exists()
        )


    def test_cleanup_rolls_back_all_database_changes_on_failure(self):
        students_queryset = Student.objects.all()
        
        with patch(
            "students.services.semester_cleanup.Student.objects.all",
            return_value=students_queryset,
        ):
            with patch.object(
                students_queryset,
                "delete",
                side_effect=RuntimeError("Simulated cleanup failure")
            ):
                with self.assertRaises(RuntimeError):
                    delete_semester_data()
        
        self.assertTrue(
            Appointment.objects.filter(pk=self.appointment.pk).exists()
        )
        self.assertTrue(
            Student.objects.filter(pk=self.student.pk).exists()
        )
        self.assertTrue(
            Slot.objects.filter(pk=self.slot.pk).exists()
        )
        self.assertTrue(
            Counselor.objects.filter(pk=self.counselor.pk).exists()
        )
