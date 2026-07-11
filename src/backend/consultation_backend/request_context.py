from contextvars import ContextVar, Token


_request_id: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


def get_request_id() -> str:
    """
    Return the request ID associated with the current request.

    Code running outside an HTTP request, such as a management command,
    receives "-" instead.
    """
    return _request_id.get()


def set_request_id(request_id: str) -> Token:
    """
    Store a request ID for the current execution context.
    """
    return _request_id.set(request_id)


def reset_request_id(token: Token) -> None:
    """
    Restore the previous request ID after the request finishes.
    """
    _request_id.reset(token)
