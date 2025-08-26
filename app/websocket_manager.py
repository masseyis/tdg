"""WebSocket manager for real-time progress updates"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Progress update data structure"""

    stage: str
    progress: int
    message: str
    timestamp: str
    task_id: Optional[str] = None
    endpoint_count: Optional[int] = None
    current_endpoint: Optional[int] = None


class WebSocketManager:
    """Manages WebSocket connections and progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, List[any]] = {}  # task_id -> list of websockets
        self.task_progress: Dict[str, ProgressUpdate] = {}
        self.task_results: Dict[str, Dict[str, str]] = {}  # task_id -> result data

    async def connect(self, websocket, task_id: str):
        """Connect a WebSocket to a specific task"""
        # Note: websocket.accept() is already called in the main.py endpoint
        # Add to active connections
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

        # Send initial progress if available
        if task_id in self.task_progress:
            try:
                await websocket.send_text(json.dumps(asdict(self.task_progress[task_id])))
            except Exception as e:
                logger.error(f"Failed to send initial progress: {e}")
                # Capture WebSocket send errors with Sentry for monitoring
                try:
                    from app.sentry import capture_exception
                    capture_exception(e, context={"task_id": task_id, "stage": "websocket_send_initial"})
                except ImportError:
                    pass  # Sentry not available

        logger.info(
            f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections[task_id])}"
        )

        try:
            # Keep connection alive and handle disconnection
            async for message in websocket:
                # Handle any client messages if needed
                pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            # Capture WebSocket errors with Sentry for monitoring
            try:
                from app.sentry import capture_exception
                capture_exception(e, context={"task_id": task_id, "stage": "websocket_manager"})
            except ImportError:
                pass  # Sentry not available
        finally:
            # Remove from active connections
            if task_id in self.active_connections:
                if websocket in self.active_connections[task_id]:
                    self.active_connections[task_id].remove(websocket)
                # Clean up empty task connections
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
            logger.info(f"WebSocket disconnected for task {task_id}")

    async def update_progress(
        self,
        task_id: str,
        stage: str,
        progress: int,
        message: str,
        endpoint_count: Optional[int] = None,
        current_endpoint: Optional[int] = None,
    ):
        """Update progress for a specific task and broadcast to all connected clients"""
        update = ProgressUpdate(
            stage=stage,
            progress=progress,
            message=message,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            endpoint_count=endpoint_count,
            current_endpoint=current_endpoint,
        )

        self.task_progress[task_id] = update
        logger.info(f"Progress update for {task_id}: {stage} - {progress}% - {message}")

        # Broadcast to all connected clients for this task
        if task_id in self.active_connections:
            disconnected_websockets = []

            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_text(json.dumps(asdict(update)))
                except Exception as e:
                    logger.error(f"Failed to send progress update to WebSocket: {e}")
                    # Capture WebSocket send errors with Sentry for monitoring
                    try:
                        from app.sentry import capture_exception
                        capture_exception(e, context={"task_id": task_id, "stage": "websocket_send_progress"})
                    except ImportError:
                        pass  # Sentry not available
                    disconnected_websockets.append(websocket)

            # Remove disconnected websockets
            for websocket in disconnected_websockets:
                if (
                    task_id in self.active_connections
                    and websocket in self.active_connections[task_id]
                ):
                    self.active_connections[task_id].remove(websocket)

            # Clean up empty task connections
            if task_id in self.active_connections and not self.active_connections[task_id]:
                del self.active_connections[task_id]

    def get_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a task"""
        return self.task_progress.get(task_id)

    def cleanup_task(self, task_id: str):
        """Clean up completed task data"""
        if task_id in self.task_progress:
            del self.task_progress[task_id]

        if task_id in self.task_results:
            del self.task_results[task_id]

        # Close all WebSocket connections for this task
        if task_id in self.active_connections:
            for websocket in self.active_connections[task_id]:
                try:
                    asyncio.create_task(websocket.close())
                except Exception as e:
                    logger.error(f"Error closing WebSocket: {e}")
                    # Capture WebSocket close errors with Sentry for monitoring
                    try:
                        from app.sentry import capture_exception
                        capture_exception(e, context={"task_id": task_id, "stage": "websocket_close"})
                    except ImportError:
                        pass  # Sentry not available
            del self.active_connections[task_id]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
