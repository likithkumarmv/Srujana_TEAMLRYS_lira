import uuid
from typing import Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

class LiraException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
        request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.request_id = request_id or str(uuid.uuid4())
        super().__init__(self.message)

class NotFoundError(LiraException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)

class VersionConflictError(LiraException):
    def __init__(self, message: str = "This case changed. Refresh and review the latest state.", details: Optional[Any] = None):
        super().__init__(code="CASE_VERSION_CONFLICT", message=message, status_code=409, details=details)

class ConflictError(LiraException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)

class UnauthorizedError(LiraException):
    def __init__(self, message: str = "Authentication credentials invalid or missing"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)

class ForbiddenError(LiraException):
    def __init__(self, message: str = "Insufficient permissions for this action"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)

class InvalidStateTransitionError(LiraException):
    def __init__(self, message: str = "Invalid case state transition"):
        super().__init__(code="INVALID_STATE_TRANSITION", message=message, status_code=409)

def create_error_response(exc: LiraException) -> JSONResponse:
    content = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "request_id": exc.request_id
        }
    }
    if exc.details is not None:
        content["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)
