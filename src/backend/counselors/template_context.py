from pydantic import BaseModel
from datetime import date, time
from counselors.models import Counselor, Slot


class SlotContext(BaseModel):
    date: date
    start_time: time
    end_time: time


class CounselorContext(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    department: str
    slots: list[SlotContext]  # slots that have no booked/pending appointment

    @classmethod
    def from_model(cls, counselor: Counselor) -> "CounselorContext":
        return cls(
            first_name=counselor.first_name,
            last_name=counselor.last_name,
            full_name=counselor.full_name,
            department=counselor.chair,
            slots=[
                SlotContext(date=s.date, start_time=s.start_time, end_time=s.end_time)
                for s in counselor.slots.exclude(
                    appointments__status__in=["booked", "pending"]
                ).distinct()
            ]
        )


class AllAvailableSlotsContext(BaseModel):
    slots: list[SlotContext]

    @classmethod
    def build(cls) -> "AllAvailableSlotsContext":
        slots = []
        for slot in Slot.objects.exclude(
            appointments__status__in=["booked", "pending"]
        ).distinct():
            slots.append(SlotContext(date=slot.date, start_time=slot.start_time, end_time=slot.end_time))
        return cls(slots=slots)
