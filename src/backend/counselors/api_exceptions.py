from consultation_backend.api_exceptions import ApplicationAPIException


class SlotOverlapWarning(ApplicationAPIException):
    status_code = 409
    default_detail = "This availability slot overlaps an existing slot."
    default_code = "slot_overlap_warning"