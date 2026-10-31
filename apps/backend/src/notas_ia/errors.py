class ChatAPIError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(ChatAPIError):
    status_code = 404
    code = "not_found"


class ConflictError(ChatAPIError):
    status_code = 409
    code = "conflict"


class InputTooLargeError(ChatAPIError):
    status_code = 413
    code = "input_too_large"


class InvalidInputError(ChatAPIError):
    status_code = 422
    code = "invalid_input"


class ProviderBadResponseError(ChatAPIError):
    status_code = 502
    code = "provider_bad_response"


class ProviderUnavailableError(ChatAPIError):
    status_code = 503
    code = "provider_unavailable"


class ProviderTimeoutError(ChatAPIError):
    status_code = 504
    code = "provider_timeout"


class ToolError(ChatAPIError):
    status_code = 502
    code = "tool_error"


class ToolUnavailableError(ChatAPIError):
    status_code = 503
    code = "tool_unavailable"
