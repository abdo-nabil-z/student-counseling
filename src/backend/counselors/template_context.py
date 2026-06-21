from pydantic import BaseModel
from datetime import date, time
from counselors.models import Counselor, Slot


class BlockContext(BaseModel):
    date: date
    start_time: time
    end_time: time


class CounselorContext(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    department: str
    slots: list[BlockContext]  # slots that have no booked/pending appointment

    @classmethod
    def from_model(cls, counselor: Counselor) -> "CounselorContext":
        return cls(
            first_name=counselor.first_name,
            last_name=counselor.last_name,
            full_name=counselor.full_name,
            department=counselor.chair,
            slots=[
                BlockContext(date=s.date, start_time=s.start_time, end_time=s.end_time)
                for s in counselor.slots.exclude(
                    appointments__status__in=["booked", "pending"]
                ).distinct()
            ]
        )


class AllAvailableBlocksContext(BaseModel):
    blocks: list[BlockContext]

    @classmethod
    def build(cls) -> "AllAvailableBlocksContext":
        blocks = []
        for slot in Slot.objects.exclude(
            appointments__status__in=["booked", "pending"]
        ).distinct():
            blocks.append(BlockContext(date=slot.date, start_time=slot.start_time, end_time=slot.end_time))
        return cls(blocks=blocks)
