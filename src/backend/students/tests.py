from datetime import time
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.models import Appointment
from counselors.models import Counselor, Slot
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
        with patch(
            "students.services.semester_cleanup.Student.delete",
            side_effect=RuntimeError("Simulated cleanup failure"),
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
