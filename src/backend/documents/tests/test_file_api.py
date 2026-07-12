from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.db.models.fields.files import FieldFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from counselors.models import Counselor
from documents.models import (
    Document,
    MasterDocument,
)
from students.models import Student


class FileAPIErrorHandlingTests(APITestCase):
    def setUp(self):
        super().setUp()

        self.media_directory = TemporaryDirectory()

        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.media_override.enable()

        self.student = Student.objects.create(
            matriculation_number="123456789",
            first_name="Test",
            last_name="Student",
            email="student@example.com",
        )

        self.counselor = Counselor.objects.create(
            title="Dr.",
            first_name="Test",
            last_name="Counselor",
            chair="Institute",
            office_address="AE22-R273",
            email="counselor@example.com",
        )

        self.master_document = (
            MasterDocument.objects.create(
                name="Test master document"
            )
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()

        super().tearDown()

    def make_uploaded_file(
        self,
        name: str,
        content: bytes = b"Test file content",
        content_type: str = (
            "application/octet-stream"
        ),
    ) -> SimpleUploadedFile:
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type=content_type,
        )

    def test_missing_student_upload_file_uses_error_contract(
        self,
    ):
        url = reverse(
            "students_api:upload-initial-study-plan",
            args=[self.student.pk],
        )

        response = self.client.post(
            url,
            data={},
            format="multipart",
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
        self.assertIn(
            "file",
            error["details"],
        )
        self.assertEqual(
            error["request_id"],
            response["X-Request-ID"],
        )

    def test_non_pdf_file_is_accepted(
        self,
    ):
        url = reverse(
            "students_api:upload-initial-study-plan",
            args=[self.student.pk],
        )

        response = self.client.post(
            url,
            data={
                "file": self.make_uploaded_file(
                    name="study-plan.txt",
                    content=b"Plain-text study plan",
                    content_type="text/plain",
                ),
                "name": "Text study plan",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.student.refresh_from_db()

        document = (
            self.student.initial_study_plan
        )

        self.assertIsNotNone(document)
        self.assertEqual(
            document.name,
            "Text study plan",
        )
        self.assertTrue(
            document.file.name.endswith(
                ".txt"
            )
        )
        self.assertTrue(
            Path(document.file.path).exists()
        )

    def test_missing_master_version_file_uses_error_contract(
        self,
    ):
        url = reverse(
            "documents_api:upload-master-version",
            args=[self.master_document.pk],
        )

        response = self.client.post(
            url,
            data={},
            format="multipart",
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
        self.assertIn(
            "file",
            error["details"],
        )

    def test_missing_physical_file_returns_controlled_404(
        self,
    ):
        document = Document.objects.create(
            file=(
                "documents/2099/01/"
                "missing-file.txt"
            ),
            name="Missing file",
        )

        url = reverse(
            "documents_api:download",
            args=[document.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "stored_file_not_found",
        )
        self.assertEqual(
            error["details"],
            {
                "resource_type": "document",
                "resource_id": document.pk,
            },
        )
        self.assertEqual(
            error["request_id"],
            response["X-Request-ID"],
        )

    def test_storage_io_error_returns_controlled_503(
        self,
    ):
        document = Document.objects.create(
            file=self.make_uploaded_file(
                "stored-file.docx"
            ),
            name="Stored file",
        )

        url = reverse(
            "documents_api:download",
            args=[document.pk],
        )

        with patch.object(
            FieldFile,
            "open",
            side_effect=OSError(
                "Simulated storage failure"
            ),
        ):
            with self.assertLogs(
                "documents.api.views",
                level="ERROR",
            ):
                response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "file_storage_unavailable",
        )
        self.assertEqual(
            error["details"],
            {
                "resource_type": "document",
                "resource_id": document.pk,
            },
        )