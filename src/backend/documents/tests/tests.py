from datetime import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from appointments.models import Appointment
from counselors.models import Counselor, Slot
from documents.models import Document
from documents.services import (
    attach_document,
    replace_attached_document,
)
from students.models import Student


class DocumentFileLifecycleTests(TestCase):
    def setUp(self):
        super().setUp()

        self.media_directory = TemporaryDirectory()

        self.media_override = override_settings(
            MEDIA_ROOT = self.media_directory.name
        )
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
    

    def make_uploaded_file(
            self,
            name: str,
            content: bytes = b"Test document content",
            content_type: str = "application/octet-stream",
    ) -> SimpleUploadedFile:
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type=content_type,
        )
    

    def create_document(self, file_name: str, display_name: str | None = None) -> Document:
        return Document.objects.create(
            file=self.make_uploaded_file(file_name),
            name=display_name or file_name,
        )
    

    def get_stored_files(self) -> set[Path]:
        media_root = Path(self.media_directory.name)

        return {
            path.resolve()
            for path in media_root.rglob("*")
            if path.is_file()
        }


    def test_successful_replacement_links_new_document_and_deletes_old_one(
        self,
    ):
        old_document = self.create_document(
            file_name="old-study-plan.docx",
            display_name="Old study plan",
        )

        self.student.initial_study_plan = old_document
        self.student.save(
            update_fields=["initial_study_plan"]
        )

        old_file_path = Path(
            old_document.file.path
        ).resolve()

        self.assertTrue(old_file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            new_document = replace_attached_document(
                instance=self.student,
                field_name="initial_study_plan",
                file=self.make_uploaded_file(
                    "new-study-plan.odt"
                ),
                name="New study plan",
            )

        self.student.refresh_from_db()

        new_file_path = Path(
            new_document.file.path
        ).resolve()

        self.assertEqual(
            self.student.initial_study_plan_id,
            new_document.pk,
        )

        self.assertFalse(
            Document.objects.filter(
                pk=old_document.pk
            ).exists()
        )

        self.assertTrue(
            Document.objects.filter(
                pk=new_document.pk
            ).exists()
        )

        self.assertFalse(old_file_path.exists())
        self.assertTrue(new_file_path.exists())



    def test_failed_replacement_keeps_old_document_and_removes_new_file(
        self,
    ):
        old_document = self.create_document(
            file_name="original-study-plan.txt",
            display_name="Original study plan",
        )

        self.student.initial_study_plan = old_document
        self.student.save(
            update_fields=["initial_study_plan"]
        )

        old_file_path = Path(
            old_document.file.path
        ).resolve()

        files_before_replacement = (
            self.get_stored_files()
        )

        with patch.object(
            self.student,
            "save",
            side_effect=RuntimeError(
                "Simulated student save failure"
            ),
        ):
            with self.assertRaises(RuntimeError):
                replace_attached_document(
                    instance=self.student,
                    field_name="initial_study_plan",
                    file=self.make_uploaded_file(
                        "failed-replacement.docx"
                    ),
                    name="Failed replacement",
                )

        self.student.refresh_from_db()

        self.assertEqual(
            self.student.initial_study_plan_id,
            old_document.pk,
        )

        self.assertTrue(
            Document.objects.filter(
                pk=old_document.pk
            ).exists()
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        self.assertTrue(old_file_path.exists())

        self.assertEqual(
            self.get_stored_files(),
            files_before_replacement,
        )



    def test_deleting_student_deletes_all_attached_documents_and_files(
        self,
    ):
        initial_study_plan = self.create_document(
            file_name="initial-study-plan.docx",
            display_name="Initial study plan",
        )

        final_study_plan = self.create_document(
            file_name="final-study-plan.xlsx",
            display_name="Final study plan",
        )

        appointment_minutes = self.create_document(
            file_name="appointment-minutes.txt",
            display_name="Appointment minutes",
        )

        self.student.initial_study_plan = (
            initial_study_plan
        )
        self.student.final_study_plan = (
            final_study_plan
        )
        self.student.save(
            update_fields=[
                "initial_study_plan",
                "final_study_plan",
            ]
        )

        appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            start_time=timezone.now(),
            duration_minutes=30,
            minutes=appointment_minutes,
        )

        student_id = self.student.pk
        appointment_id = appointment.pk

        document_ids = {
            initial_study_plan.pk,
            final_study_plan.pk,
            appointment_minutes.pk,
        }

        file_paths = {
            Path(initial_study_plan.file.path).resolve(),
            Path(final_study_plan.file.path).resolve(),
            Path(appointment_minutes.file.path).resolve(),
        }

        for file_path in file_paths:
            self.assertTrue(file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            self.student.delete()

        self.assertFalse(
            Student.objects.filter(
                pk=student_id
            ).exists()
        )

        self.assertFalse(
            Appointment.objects.filter(
                pk=appointment_id
            ).exists()
        )

        self.assertTrue(
            Counselor.objects.filter(
                pk=self.counselor.pk
            ).exists()
        )

        self.assertFalse(
            Document.objects.filter(
                pk__in=document_ids
            ).exists()
        )

        for file_path in file_paths:
            self.assertFalse(file_path.exists())


    def test_deleting_appointment_deletes_minutes_document_and_file(
        self,
    ):
        appointment_minutes = self.create_document(
            file_name="direct-appointment-minutes.rtf",
            display_name="Appointment minutes",
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

        file_path = Path(
            appointment_minutes.file.path
        ).resolve()

        self.assertTrue(file_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            appointment.delete()

        self.assertFalse(
            Appointment.objects.filter(
                pk=appointment_id
            ).exists()
        )

        self.assertFalse(
            Document.objects.filter(
                pk=document_id
            ).exists()
        )

        self.assertFalse(file_path.exists())

        self.assertTrue(
            Student.objects.filter(
                pk=self.student.pk
            ).exists()
        )

        self.assertTrue(
            Counselor.objects.filter(
                pk=self.counselor.pk
            ).exists()
        )