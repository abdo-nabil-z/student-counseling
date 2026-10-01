from pydantic import BaseModel, field_serializer
from datetime import date, time, timedelta

from django.utils import timezone

from appointments.models import Appointment


class AppointmentContext(BaseModel):
    date: date
    start_time: time
    end_time: time
    location: str
    status: str

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        # templates should only ever show hours:minutes, never seconds
        return value.strftime("%H:%M")

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
