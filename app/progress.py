"""
Progress callback system for test case generation

This module provides a clean interface for progress reporting that separates
concerns between AI providers and the HTTP/WebSocket layer.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class ProgressCallback(ABC):
    """Abstract base class for progress callbacks"""
    
    @abstractmethod
    async def update(self, stage: str, progress: int, message: str, **kwargs) -> None:
        """
        Update progress
        
        Args:
            stage: Current stage (parsing, generating, enhancing, etc.)
            progress: Progress percentage (0-100)
            message: Human-readable progress message
            **kwargs: Additional context (endpoint_count, current_endpoint, etc.)
        """
        pass


class NoOpProgressCallback(ProgressCallback):
    """No-op progress callback for when progress tracking is not needed"""
    
    async def update(self, stage: str, progress: int, message: str, **kwargs) -> None:
        """Do nothing - progress updates are ignored"""
        pass


class LoggingProgressCallback(ProgressCallback):
    """Progress callback that logs progress updates"""
    
    async def update(self, stage: str, progress: int, message: str, **kwargs) -> None:
        """Log progress updates"""
        logger.info(f"Progress [{stage}] {progress}%: {message}")


class WebSocketProgressCallback(ProgressCallback):
    """Progress callback that sends updates via WebSocket"""
    
    def __init__(self, task_id: str, update_progress_func: Callable):
        """
        Initialize WebSocket progress callback
        
        Args:
            task_id: Task ID for WebSocket updates
            update_progress_func: Function to call for WebSocket updates
        """
        self.task_id = task_id
        self.update_progress_func = update_progress_func
    
    async def update(self, stage: str, progress: int, message: str, **kwargs) -> None:
        """Send progress update via WebSocket"""
        try:
            await self.update_progress_func(
                self.task_id, 
                stage, 
                progress, 
                message,
                endpoint_count=kwargs.get('endpoint_count'),
                current_endpoint=kwargs.get('current_endpoint')
            )
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")


def create_progress_callback(task_id: Optional[str] = None, update_progress_func: Optional[Callable] = None) -> ProgressCallback:
    """
    Create appropriate progress callback based on context
    
    Args:
        task_id: Task ID for WebSocket updates (if None, uses logging)
        update_progress_func: Function to call for WebSocket updates
        
    Returns:
        ProgressCallback instance
    """
    if task_id and update_progress_func:
        return WebSocketProgressCallback(task_id, update_progress_func)
    else:
        return LoggingProgressCallback()
