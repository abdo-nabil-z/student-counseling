from consultation_backend.api_exceptions import ApplicationAPIException


class EmailDeliveryNotEditable(ApplicationAPIException):
    status_code = 409
    default_detail = ("This email delivery can no longer be edited.")
    default_code = "email_delivery_not_editable"


class EmailBatchNotSendable(ApplicationAPIException):
    status_code = 409
    default_detail= ("This email batch cannot be queued for sending.")
    default_code = "email_batch_not_sendable"


class EmailDeliveryNotResendable(
    ApplicationAPIException
):
    status_code = 409
    default_detail = (
        "This email delivery cannot be resent."
    )
    default_code = "email_delivery_not_resendable"


class EmailTemplateNotConfigured(ApplicationAPIException):
    status_code = 409
    default_detail = (
        "The required email template is not configured."
    )
    default_code = "email_template_not_configured"