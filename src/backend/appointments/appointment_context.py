from pydantic import BaseModel
from datetime import date, time, timedelta

from django.utils import timezone

from appointments.models import Appointment


class AppointmentContext(BaseModel):
    date: date
    start_time: time
    end_time: time
    location: str
    status: str

    @classmethod
    def from_model(cls, appointment: Appointment) -> "AppointmentContext":
        start_time = timezone.localtime(appointment.start_time)
        end_time = start_time + timedelta(
            minutes=appointment.duration_minutes
        )

        return cls(
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time(),
            location=appointment.location or "",
            status=appointment.status,
        )
