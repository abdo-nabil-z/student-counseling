from pydantic import BaseModel
from datetime import date, time

from appointments.models import Appointment


class AppointmentContext(BaseModel):
    date: date
    start_time: time
    end_time: time
    location: str
    status: str

    @classmethod
    def from_model(cls, appointment: Appointment) -> "AppointmentContext":
        return cls(
            date=appointment.start_time.date(),
            start_time=appointment.start_time.time(),
            end_time=appointment.end_time.time(),
            location=appointment.location or "",
            status=appointment.status,
        )
