"""Custom exception classes for pipeline errors."""


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


class ScraperError(PipelineError):
    """Exception raised for scraper-related errors."""

    pass


class ProcessorError(PipelineError):
    """Exception raised for processing-related errors."""

    pass


class EmbeddingError(PipelineError):
    """Exception raised for embedding generation errors."""

    pass


class StorageError(PipelineError):
    """Exception raised for storage-related errors."""

    pass

