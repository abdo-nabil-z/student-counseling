from datetime import date, time

from django.utils import timezone
from pydantic import BaseModel, field_serializer

from counselors.models import Counselor
from counselors.services.slot_status import (
    build_all_counselor_slot_statuses,
    build_counselor_slot_status,
)


class SlotContext(BaseModel):
    date: date
    start_time: time
    end_time: time

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        # templates should only ever show hours:minutes, never seconds
        return value.strftime("%H:%M")


def _free_slot_contexts(status_data):
    free_slots = []

    for slot in status_data["slots"]:
        for segment in slot["segments"]:
            if segment["status"] != "free":
                continue

            start = timezone.localtime(
                segment["start"]
            )

            end = timezone.localtime(
                segment["end"]
            )

            free_slots.append(
                SlotContext(
                    date=start.date(),
                    start_time=start.time(),
                    end_time=end.time(),
                )
            )

    return free_slots


class CounselorContext(BaseModel):
    title: str
    first_name: str
    last_name: str
    full_name: str
    department: str
    office_address: str
    email: str
    slots: list[SlotContext]

    @classmethod
    def from_model(
        cls,
        counselor: Counselor,
    ) -> "CounselorContext":
        slot_status = build_counselor_slot_status(
            counselor
        )

        return cls(
            title=counselor.title,
            first_name=counselor.first_name,
            last_name=counselor.last_name,
            full_name=counselor.full_name,
            department=counselor.chair,
            office_address=counselor.office_address,
            email=counselor.email,
            slots=_free_slot_contexts(
                slot_status
            ),
        )


class AllAvailableSlotsContext(BaseModel):
    slots: list[SlotContext]

    @classmethod
    def build(cls) -> "AllAvailableSlotsContext":
        slots = []

        for status_data in (
            build_all_counselor_slot_statuses()
        ):
            slots.extend(
                _free_slot_contexts(
                    status_data
                )
            )

        return cls(slots=slots)