class GenBIException(Exception):
    pass

class SQLValidationError(GenBIException):
    pass

class LLMTimeoutError(GenBIException):
    pass

class ManifestNotFoundError(GenBIException):
    pass

class DatabaseError(GenBIException):
    pass

class AuthError(GenBIException):
    pass

class RateLimitError(GenBIException):
    pass

class RAGError(GenBIException):
    pass

class ForbiddenError(GenBIException):
    pass
