from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


class UserAlreadyExistsError(BaseHTTPException):
    def __init__(self, detail: str = "User with this email already exists") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsError(BaseHTTPException):
    def __init__(self, detail: str = "Invalid email or password") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidTokenError(BaseHTTPException):
    def __init__(self, detail: str = "Invalid token") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenExpiredError(BaseHTTPException):
    def __init__(self, detail: str = "Token has expired") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class UserNotFoundError(BaseHTTPException):
    def __init__(self, detail: str = "User not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PermissionDeniedError(BaseHTTPException):
    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)