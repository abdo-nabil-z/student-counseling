from consultation_backend.api_exceptions import ApplicationAPIException


class AppointmentOverlapWarning(ApplicationAPIException):
    status_code = 409
    default_detail = (
        "This appointment overlaps another active appointment "
        "for the same counselor."
    )
    default_code = "appointment_overlap_warning"