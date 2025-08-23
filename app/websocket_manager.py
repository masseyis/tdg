"""WebSocket manager for real-time progress updates"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    stage: str
    progress: int
    message: str
    timestamp: str
    endpoint_count: Optional[int] = None
    current_endpoint: Optional[int] = None

class WebSocketManager:
    """Manages WebSocket connections and progress updates"""
    
    def __init__(self):
        self.active_connections: Set[str] = set()
        self.task_progress: Dict[str, ProgressUpdate] = {}
        self.connection_tasks: Dict[str, str] = {}  # connection_id -> task_id
    
    async def connect(self, websocket, task_id: str):
        """Connect a WebSocket to a specific task"""
        connection_id = str(uuid.uuid4())
        self.active_connections.add(connection_id)
        self.connection_tasks[connection_id] = task_id
        
        # Send initial progress if available
        if task_id in self.task_progress:
            await websocket.send_text(json.dumps(self.task_progress[task_id].__dict__))
        
        try:
            # Keep connection alive and handle disconnection
            async for message in websocket:
                # Handle any client messages if needed
                pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.active_connections.discard(connection_id)
            if connection_id in self.connection_tasks:
                del self.connection_tasks[connection_id]
    
    def update_progress(self, task_id: str, stage: str, progress: int, message: str, 
                       endpoint_count: Optional[int] = None, current_endpoint: Optional[int] = None):
        """Update progress for a specific task"""
        update = ProgressUpdate(
            stage=stage,
            progress=progress,
            message=message,
            timestamp=datetime.now().isoformat(),
            endpoint_count=endpoint_count,
            current_endpoint=current_endpoint
        )
        
        self.task_progress[task_id] = update
        logger.info(f"Progress update for {task_id}: {stage} - {progress}% - {message}")
    
    def get_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a task"""
        return self.task_progress.get(task_id)
    
    def cleanup_task(self, task_id: str):
        """Clean up completed task data"""
        if task_id in self.task_progress:
            del self.task_progress[task_id]
        
        # Remove any connections associated with this task
        connections_to_remove = [
            conn_id for conn_id, task in self.connection_tasks.items() 
            if task == task_id
        ]
        for conn_id in connections_to_remove:
            if conn_id in self.connection_tasks:
                del self.connection_tasks[conn_id]

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
