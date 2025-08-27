"""
Generation Service with Priority Queue

This service manages test generation requests with different priority levels.
It uses a separate thread pool to prevent blocking the main web server threads.

Priority levels:
- HIGH: Premium users, immediate processing
- NORMAL: Standard users, normal queue
- LOW: Free tier, processed when resources available
"""

import asyncio
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue
from typing import Any, Callable, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Priority levels for generation requests"""
    LOW = 3
    NORMAL = 2
    HIGH = 1


@dataclass
class GenerationRequest:
    """A generation request with priority"""
    task_id: str
    priority: Priority
    request_data: Any
    progress_callback: Callable
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """Priority queue ordering: lower priority number = higher priority"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # If same priority, FIFO (earlier timestamp first)
        return self.timestamp < other.timestamp


class GenerationService:
    """
    Service for managing test generation with priority queuing.
    
    Uses a separate thread pool to prevent blocking the main web server.
    Supports different priority levels for future tiered pricing.
    """
    
    def __init__(self, max_workers: int = 2, queue_size: int = 100):
        """
        Initialize the generation service.
        
        Args:
            max_workers: Number of worker threads for generation
            queue_size: Maximum number of queued requests
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        
        # Priority queue for generation requests
        self.request_queue = PriorityQueue(maxsize=queue_size)
        
        # Thread pool for generation workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="generation-worker"
        )
        
        # Track active tasks
        self.active_tasks: Dict[str, GenerationRequest] = {}
        self.completed_tasks: Dict[str, Any] = {}
        
        # Service state
        self.running = False
        self.worker_thread = None
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "queue_size": 0,
            "active_workers": 0,
        }
        
        logger.info(f"Generation service initialized with {max_workers} workers, queue size {queue_size}")
    
    def start(self):
        """Start the generation service worker thread"""
        if self.running:
            logger.warning("Generation service already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="generation-service-worker",
            daemon=True
        )
        self.worker_thread.start()
        logger.info("Generation service started")
    
    def stop(self):
        """Stop the generation service"""
        if not self.running:
            return
        
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        logger.info("Generation service stopped")
    
    def submit_request(
        self,
        request_data: Any,
        progress_callback: Callable,
        priority: Priority = Priority.NORMAL,
        task_id: Optional[str] = None
    ) -> str:
        """
        Submit a generation request to the queue.
        
        Args:
            request_data: The generation request data
            progress_callback: Callback for progress updates
            priority: Request priority level
            task_id: Optional task ID (generated if not provided)
            
        Returns:
            Task ID for tracking the request
            
        Raises:
            QueueFullError: If the queue is full
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        request = GenerationRequest(
            task_id=task_id,
            priority=priority,
            request_data=request_data,
            progress_callback=progress_callback
        )
        
        try:
            self.request_queue.put_nowait(request)
            self.active_tasks[task_id] = request
            self.stats["total_requests"] += 1
            self.stats["queue_size"] = self.request_queue.qsize()
            
            logger.info(f"Submitted generation request {task_id} with priority {priority.name}")
            return task_id
            
        except queue.Full:
            logger.error(f"Generation queue is full, rejecting request {task_id}")
            raise QueueFullError("Generation queue is full")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task"""
        if task_id in self.active_tasks:
            request = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "queued",
                "priority": request.priority.name,
                "timestamp": request.timestamp,
                "queue_position": self._get_queue_position(task_id)
            }
        elif task_id in self.completed_tasks:
            return {
                "task_id": task_id,
                "status": "completed",
                "result": self.completed_tasks[task_id]
            }
        else:
            return None
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "queue_size": self.request_queue.qsize(),
            "active_workers": len([f for f in self.executor._threads if f.is_alive()]),
            "running": self.running
        }
    
    def _worker_loop(self):
        """Main worker loop that processes queued requests"""
        logger.info("Generation service worker loop started")
        
        while self.running:
            try:
                # Get next request from queue (blocking with timeout)
                try:
                    request = self.request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the request
                self._process_request(request)
                
            except Exception as e:
                logger.error(f"Error in generation worker loop: {e}")
                time.sleep(1)  # Avoid tight error loop
        
        logger.info("Generation service worker loop stopped")
    
    def _process_request(self, request: GenerationRequest):
        """Process a single generation request"""
        task_id = request.task_id
        logger.info(f"Processing generation request {task_id} with priority {request.priority.name}")
        
        try:
            # Update stats
            self.stats["active_workers"] += 1
            
            # Run generation in thread pool
            future = self.executor.submit(
                self._run_generation,
                request.request_data,
                request.progress_callback
            )
            
            # Wait for completion
            result = future.result()
            
            # Mark as completed
            self.completed_tasks[task_id] = result
            self.stats["completed_requests"] += 1
            
            logger.info(f"Generation request {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Generation request {task_id} failed: {e}")
            self.stats["failed_requests"] += 1
            
            # Store error result
            self.completed_tasks[task_id] = {"error": str(e)}
            
        finally:
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.stats["active_workers"] -= 1
            self.stats["queue_size"] = self.request_queue.qsize()
    
    def _run_generation(self, request_data: Any, progress_callback: Callable) -> Any:
        """
        Run the actual generation process.
        
        This runs in a separate thread to avoid blocking the main event loop.
        """
        # Import here to avoid circular imports
        from app.generation.cases import generate_test_cases_with_progress
        from app.utils.openapi_loader import load_openapi_spec
        from app.utils.openapi_normalizer import normalize_openapi
        from app.utils.zipping import create_artifact_zip
        from app.websocket_manager import websocket_manager
        import tempfile
        from pathlib import Path
        import gc
        
        # Extract data from request
        task_id = request_data.get("task_id")
        openapi_data = request_data.get("openapi")
        cases_per_endpoint = request_data.get("cases_per_endpoint", 10)
        outputs = request_data.get("outputs", ["junit", "python", "nodejs", "postman"])
        domain_hint = request_data.get("domain_hint")
        seed = request_data.get("seed")
        ai_speed = request_data.get("ai_speed", "fast")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Send initial progress
            loop.run_until_complete(
                progress_callback("parsing", 10, "Parsing OpenAPI specification...")
            )
            
            # Load and normalize the spec
            spec = loop.run_until_complete(load_openapi_spec(openapi_data))
            normalized = normalize_openapi(spec)
            
            loop.run_until_complete(
                progress_callback("parsing", 100, "OpenAPI specification parsed successfully")
            )
            
            loop.run_until_complete(
                progress_callback("generating", 20, f"Generating test cases for {len(normalized.endpoints)} endpoints...")
            )
            
            # Generate test cases with detailed progress
            loop.run_until_complete(
                progress_callback("generating", 30, "Starting AI generation...")
            )
            
            artifacts = loop.run_until_complete(
                generate_test_cases_with_progress(
                    task_id=task_id,
                    normalized_spec=normalized,
                    cases_per_endpoint=cases_per_endpoint,
                    outputs=outputs,
                    domain_hint=domain_hint,
                    seed=seed,
                    ai_speed=ai_speed
                )
            )
            
            loop.run_until_complete(
                progress_callback("generating", 100, "Test cases generated successfully")
            )
            
            loop.run_until_complete(
                progress_callback("zipping", 20, "Creating ZIP file...")
            )
            
            # Create ZIP file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                zip_path = Path(tmp.name)
                create_artifact_zip(artifacts, zip_path)
            
            loop.run_until_complete(
                progress_callback("zipping", 100, "ZIP file created successfully")
            )
            
            loop.run_until_complete(
                progress_callback("complete", 100, "Generation complete! ZIP file ready for download.")
            )
            
            # Store the ZIP file path for later retrieval
            websocket_manager.task_results[task_id] = {"zip_path": str(zip_path)}
            
            # Clean up memory after generation
            del artifacts
            gc.collect()
            
            return {"status": "success", "zip_path": str(zip_path)}
            
        except Exception as e:
            # Send error progress
            try:
                loop.run_until_complete(
                    progress_callback("error", 0, f"Generation failed: {str(e)}")
                )
            except:
                pass  # Ignore errors in error reporting
            
            return {"status": "error", "error": str(e)}
            
        finally:
            loop.close()
    
    def _get_queue_position(self, task_id: str) -> Optional[int]:
        """Get the position of a task in the queue (approximate)"""
        # This is a simplified implementation
        # In a real system, you might want to track this more precisely
        return None


class QueueFullError(Exception):
    """Raised when the generation queue is full"""
    pass


# Global generation service instance
generation_service: Optional[GenerationService] = None


def get_generation_service() -> GenerationService:
    """Get the global generation service instance"""
    global generation_service
    if generation_service is None:
        # Import here to avoid circular imports
        from app.config import settings
        
        generation_service = GenerationService(
            max_workers=settings.generation_workers,
            queue_size=settings.generation_queue_size
        )
        generation_service.start()
    
    return generation_service


def shutdown_generation_service():
    """Shutdown the global generation service"""
    global generation_service
    if generation_service:
        generation_service.stop()
        generation_service = None
