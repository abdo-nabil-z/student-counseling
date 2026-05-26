from pydantic import BaseModel
from datetime import date, time
from counselors.models import Counselor, AppointmentSlot


class BlockContext(BaseModel):
    date: date
    start_time: time
    end_time: time


class CounselorContext(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    department: str
    availability_blocks: list[BlockContext]  # blocks that have at least one available slot

    @classmethod
    def from_model(cls, counselor: Counselor) -> "CounselorContext":
        return cls(
            first_name=counselor.first_name,
            last_name=counselor.last_name,
            full_name=counselor.full_name,
            department=counselor.chair,
            availability_blocks=[
                BlockContext(date=b.date, start_time=b.start_time, end_time=b.end_time)
                for b in counselor.availability_blocks.filter(
                    appointment_slots__status=AppointmentSlot.Status.AVAILABLE
                ).distinct()
            ]
        )
        
        
class AllAvailableBlocksContext(BaseModel):
    blocks: list[BlockContext]
    
    @classmethod
    def build(cls) -> "AllAvailableBlocksContext":
        blocks = []
        for block in AppointmentSlot.objects.filter(status=AppointmentSlot.Status.AVAILABLE).select_related("availability_block").distinct():
            b = block.availability_block
            blocks.append(BlockContext(date=b.date, start_time=b.start_time, end_time=b.end_time))
        return cls(blocks=blocks)

    