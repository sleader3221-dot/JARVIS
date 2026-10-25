"""Minimal stand-in for the `anthropic` exception classes, used only when the SDK isn't installed."""


class APIError(Exception):
    def __init__(self, message, request=None, *, body=None):
        super().__init__(message)
        self.message = message
        self.request = request
        self.body = body


class APIConnectionError(APIError):
    def __init__(self, *, message="Connection error.", request=None):
        super().__init__(message, request, body=None)


class APIStatusError(APIError):
    def __init__(self, message, *, response, body):
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class BadRequestError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    pass


class InternalServerError(APIStatusError):
    pass


class Anthropic:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("anthropic SDK is not installed")
