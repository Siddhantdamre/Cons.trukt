"""Shared exception types for the Cons.trukt pipeline."""


class ConsTruktError(Exception):
    """Base exception for application-level errors."""


class ConfigError(ConsTruktError):
    """Raised when configuration is missing or invalid."""


class ExtractionError(ConsTruktError):
    """Raised when blueprint text extraction fails."""


class RetrievalError(ConsTruktError):
    """Raised when vector retrieval or ingestion fails."""


class IngestionError(RetrievalError):
    """Raised when local data ingestion cannot proceed."""


class ModelBackendError(ConsTruktError):
    """Raised when an LLM backend cannot produce usable output."""


class ParsingError(ConsTruktError):
    """Raised when model output cannot be parsed into tasks."""


class StorageError(ConsTruktError):
    """Raised when task persistence or audit retrieval fails."""
