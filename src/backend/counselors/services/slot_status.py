from django.utils import timezone

from appointments.models import Appointment
from counselors.models import Counselor, Slot

from datetime import datetime, timedelta


def _make_slot_datetime(slot_date, slot_time):
    value = datetime.combine(slot_date, slot_time)

    if timezone.is_naive(value):
        return timezone.make_aware(value)

    return value


def _appointment_end_time(appointment):
    return appointment.start_time + timedelta(minutes=appointment.duration_minutes)


def _student_data(student):
    return {
        "id": student.id,
        "matriculation_number": student.matriculation_number,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "full_name": student.full_name,
    }


def _appointment_data(appointment):
    return {
        "id": appointment.id,
        "status": appointment.status,
        "start_time": appointment.start_time,
        "duration_minutes": appointment.duration_minutes,
        "end_time": _appointment_end_time(appointment),
        "location": appointment.location,
        "student": _student_data(appointment.student),
    }


def _counselor_data(counselor):
    return {
        "id": counselor.id,
        "title": counselor.title,
        "first_name": counselor.first_name,
        "last_name": counselor.last_name,
        "full_name": counselor.full_name,
        "email": counselor.email,
        "office_address": counselor.office_address,
    }


def _slot_start_datetime(slot):
    return _make_slot_datetime(slot.date, slot.start_time)


def _slot_end_datetime(slot):
    return _make_slot_datetime(slot.date, slot.end_time)


def _appointment_overlaps_slot(appointment, slot):
    appointment_start = appointment.start_time
    appointment_end = _appointment_end_time(appointment)

    slot_start = _slot_start_datetime(slot)
    slot_end = _slot_end_datetime(slot)

    return appointment_start < slot_end and appointment_end > slot_start


def _build_segments_for_slot(slot, appointments):
    slot_start = _slot_start_datetime(slot)
    slot_end = _slot_end_datetime(slot)

    overlapping_appointments = [
        appointment
        for appointment in appointments
        if _appointment_overlaps_slot(appointment, slot)
    ]

    segments = []
    cursor = slot_start

    for appointment in overlapping_appointments:
        appointment_start = appointment.start_time
        appointment_end = _appointment_end_time(appointment)

        taken_start = max(appointment_start, slot_start)
        taken_end = min(appointment_end, slot_end)

        if taken_start >= taken_end:
            continue

        if cursor < taken_start:
            segments.append(
                {
                    "status": "free",
                    "start": cursor,
                    "end": taken_start,
                    "appointment": None,
                }
            )

        if cursor < taken_end:
            segments.append(
                {
                    "status": "taken",
                    "start": max(cursor, taken_start),
                    "end": taken_end,
                    "appointment": _appointment_data(appointment),
                }
            )

        cursor = max(cursor, taken_end)

    if cursor < slot_end:
        segments.append(
            {
                "status": "free",
                "start": cursor,
                "end": slot_end,
                "appointment": None,
            }
        )

    return segments


def _appointment_is_covered_by_any_slot(appointment, slots):
    return any(
        _appointment_overlaps_slot(appointment, slot)
        for slot in slots
    )


def build_counselor_slot_status(counselor):
    slots = list(
        Slot.objects
        .filter(counselor=counselor)
        .order_by("date", "start_time")
    )

    appointments = list(
        Appointment.objects
        .filter(counselor=counselor)
        .select_related("student", "counselor", "slot")
        .order_by("start_time")
    )

    return {
        "counselor": _counselor_data(counselor),
        "slots": [
            {
                "id": slot.id,
                "date": slot.date,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "segments": _build_segments_for_slot(slot, appointments),
            }
            for slot in slots
        ],
        "uncovered_appointments": [
            _appointment_data(appointment)
            for appointment in appointments
            if not _appointment_is_covered_by_any_slot(appointment, slots)
        ],
    }


def build_all_counselor_slot_statuses():
    counselors = Counselor.objects.all().order_by("id")

    return [
        build_counselor_slot_status(counselor)
        for counselor in counselors
    ]
