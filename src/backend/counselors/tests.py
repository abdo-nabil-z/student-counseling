from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework.test import APITestCase

from appointments.models import Appointment
from counselors.models import Counselor, Slot
from counselors.services.slot_status import (
    build_counselor_slot_status,
)
from students.models import Student


class AvailabilitySlotAPITests(APITestCase):
    def setUp(self):
        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Slot",
            last_name="Test",
            chair="Institute",
            office_address="Room 1",
            email="slot@example.com",
        )

    def test_same_counselor_can_have_overlapping_availability_slots(self):
        first_response = self.client.post(
            f"/api/counselors/{self.counselor.pk}/slots/",
            {
                "date": "2026-09-28",
                "start_time": "10:00",
                "end_time": "12:00",
            },
            format="json",
        )

        second_response = self.client.post(
            f"/api/counselors/{self.counselor.pk}/slots/",
            {
                "date": "2026-09-28",
                "start_time": "11:00",
                "end_time": "13:00",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        self.assertEqual(
            second_response.status_code,
            201,
        )

        self.assertEqual(
            Slot.objects.filter(
                counselor=self.counselor
            ).count(),
            2,
        )



class CounselorAvailabilityStatusTests(TestCase):
    def setUp(self):
        self.berlin = ZoneInfo("Europe/Berlin")

        self.counselor = Counselor.objects.create(
            title="Prof.",
            first_name="Availability",
            last_name="Test",
            chair="Institute",
            office_address="Room 1",
            email="availability@example.com",
        )

        self.student = Student.objects.create(
            matriculation_number="500000001",
            first_name="Availability",
            last_name="Student",
            email="availability.student@example.com",
        )

        self.slot = Slot.objects.create(
            counselor=self.counselor,
            date="2026-09-28",
            start_time="10:00",
            end_time="11:00",
        )

    def test_cancelled_appointment_does_not_occupy_slot(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.CANCELLED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        segments = result["slots"][0]["segments"]

        self.assertEqual(len(segments), 1)
        self.assertEqual(
            segments[0]["status"],
            "free",
        )

        self.assertEqual(
            segments[0]["start"].strftime("%H:%M"),
            "10:00",
        )

        self.assertEqual(
            segments[0]["end"].strftime("%H:%M"),
            "11:00",
        )

    def test_missed_appointment_does_not_occupy_slot(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.MISSED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        self.assertEqual(
            result["slots"][0]["segments"][0]["status"],
            "free",
        )

    def test_completed_appointment_does_not_occupy_slot(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.COMPLETED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        self.assertEqual(
            result["slots"][0]["segments"][0]["status"],
            "free",
        )

    def test_booked_appointment_splits_slot_into_free_taken_free(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        segments = result["slots"][0]["segments"]

        self.assertEqual(
            [
                segment["status"]
                for segment in segments
            ],
            [
                "free",
                "taken",
                "free",
            ],
        )

        self.assertEqual(
            segments[0]["start"].strftime("%H:%M"),
            "10:00",
        )

        self.assertEqual(
            segments[0]["end"].strftime("%H:%M"),
            "10:15",
        )

        self.assertEqual(
            segments[1]["start"].strftime("%H:%M"),
            "10:15",
        )

        self.assertEqual(
            segments[1]["end"].strftime("%H:%M"),
            "10:45",
        )

        self.assertEqual(
            segments[2]["start"].strftime("%H:%M"),
            "10:45",
        )

        self.assertEqual(
            segments[2]["end"].strftime("%H:%M"),
            "11:00",
        )

    def test_pending_appointment_occupies_slot(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.PENDING,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        statuses = [
            segment["status"]
            for segment in result["slots"][0]["segments"]
        ]

        self.assertIn(
            "taken",
            statuses,
        )

    def test_other_counselor_appointment_does_not_affect_slot(self):
        other_counselor = Counselor.objects.create(
            title="Dr.",
            first_name="Other",
            last_name="Counselor",
            chair="Institute",
            office_address="Room 2",
            email="other@example.com",
        )

        Appointment.objects.create(
            student=self.student,
            counselor=other_counselor,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        segments = result["slots"][0]["segments"]

        self.assertEqual(len(segments), 1)
        self.assertEqual(
            segments[0]["status"],
            "free",
        )

    def test_appointment_without_slot_still_occupies_overlapping_time(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=None,
            start_time=datetime(
                2026,
                9,
                28,
                10,
                15,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        statuses = [
            segment["status"]
            for segment in result["slots"][0]["segments"]
        ]

        self.assertEqual(
            statuses,
            [
                "free",
                "taken",
                "free",
            ],
        )

    def test_outside_appointment_is_reported_as_uncovered(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=None,
            start_time=datetime(
                2026,
                9,
                28,
                14,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        self.assertEqual(
            len(result["uncovered_appointments"]),
            1,
        )

        self.assertEqual(
            result["uncovered_appointments"][0][
                "student"
            ]["id"],
            self.student.pk,
        )

    def test_cancelled_outside_appointment_is_not_uncovered(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=None,
            start_time=datetime(
                2026,
                9,
                28,
                14,
                0,
                tzinfo=self.berlin,
            ),
            duration_minutes=30,
            status=Appointment.Status.CANCELLED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        self.assertEqual(
            result["uncovered_appointments"],
            [],
        )

    def test_slot_status_converts_utc_to_berlin_time(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            slot=self.slot,
            start_time=datetime(
                2026,
                9,
                28,
                8,
                15,
                tzinfo=ZoneInfo("UTC"),
            ),
            duration_minutes=30,
            status=Appointment.Status.BOOKED,
        )

        result = build_counselor_slot_status(
            self.counselor
        )

        taken_segment = next(
            segment
            for segment in result["slots"][0]["segments"]
            if segment["status"] == "taken"
        )

        self.assertEqual(
            taken_segment["start"].strftime("%H:%M"),
            "10:15",
        )

        self.assertEqual(
            taken_segment["end"].strftime("%H:%M"),
            "10:45",
        )