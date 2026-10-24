class AppError(Exception):
    pass


class ValidationError(AppError):
    pass


class DuplicateError(AppError):
    pass


class NotFoundError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass


class DataFileError(AppError):
    pass
