"""Base client interface for all integrations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry failed operations.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator


class BaseIntegrationClient(ABC):
    """Abstract base class for integration clients."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the client.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._connected = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the service.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the service.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the service is healthy and reachable.

        Returns:
            True if service is healthy, False otherwise
        """
        pass

    def is_connected(self) -> bool:
        """
        Check if client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
