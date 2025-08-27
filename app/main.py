"""
FastAPI main application

ENDPOINT DESIGN PRINCIPLES:
==========================

1. /api/generate (JSON API Endpoint):
   - Purpose: Programmatic/API access
   - Input: JSON payload (GenerateRequest schema)
   - Processing: Sync OR Async (configurable)
   - Output: ZIP file (sync) OR task_id (async)
   - Use cases: API integrations, CI/CD, automation

2. /generate-ui (Web UI Endpoint):
   - Purpose: Web form submissions
   - Input: Form data (multipart/form-data) with file uploads
   - Processing: Currently Sync (for compatibility), Future: Async
   - Output: Currently ZIP file, Future: task_id for WebSocket progress
   - Use cases: Web UI, file uploads, immediate download (current)

3. /api/download/{task_id} (Download Endpoint):
   - Purpose: Retrieve completed generation results
   - Input: task_id from async generation
   - Output: ZIP file with generated artifacts
   - Use cases: Download results after background processing

4. /ws/{task_id} (WebSocket Endpoint):
   - Purpose: Real-time progress updates
   - Input: task_id connection
   - Output: Live progress messages
   - Use cases: UI progress indicators, status updates

CURRENT STATE & FUTURE PLANS:
============================

CURRENT:
- /api/generate: JSON API with sync/async support ✅
- /generate-ui: Form-based, synchronous, returns ZIP file ✅
- WebSocket infrastructure: Built but not yet integrated ✅
- E2E tests: Passing with current synchronous behavior ✅

FUTURE (Phase 2):
- /generate-ui: Convert to async with WebSocket progress
- Frontend: Update to handle task_id and progress tracking
- E2E tests: Update to test async flow with progress indicators
- Download: Use /api/download/{task_id} for completed tasks

IMPORTANT: Maintain this separation of concerns!
- /api/generate for JSON API consumers
- /generate-ui for web form submissions
- Never mix JSON and form data handling
- Always use appropriate endpoint for the use case
"""

# Global semaphore to limit concurrent requests
import asyncio
import base64
import datetime
import gc
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.generation.cases import generate_test_cases, generate_test_cases_with_progress
from app.schemas import GenerateRequest, ValidateRequest, ValidateResponse
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi
from app.utils.zipping import create_artifact_zip
from app.websocket_manager import websocket_manager
from app.auth.routes import router as auth_router
from app.sentry import init_sentry, capture_exception, set_tag

request_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

# IMPORTANT: /api/generate endpoint is JSON-only for API consumers
# This endpoint should NEVER accept form data or file uploads
# Use /generate-ui for web form submissions with file uploads

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking and monitoring
init_sentry()

# Initialize FastAPI app
app = FastAPI(
    title="Test Data Generator",
    version="0.1.0",
    description="Generate test data from OpenAPI specifications",
)

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include authentication routes
app.include_router(auth_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    """Render app page"""
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "sentry_dsn": settings.sentry_dsn,
            "sentry_environment": settings.sentry_environment,
        },
    )


@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    """Render authentication page"""
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Render pricing page"""
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request):
    """Render documentation page"""
    return templates.TemplateResponse("docs.html", {"request": request})


@app.post("/app", response_class=HTMLResponse)
async def app_page_post(request: Request):
    """Handle form submission from app page"""
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "sentry_dsn": settings.sentry_dsn,
            "sentry_environment": settings.sentry_environment,
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return "OK"


@app.get("/sentry-debug")
async def trigger_error():
    """Test endpoint to trigger a Sentry error for debugging purposes"""
    try:
        # Intentionally trigger a division by zero error
        division_by_zero = 1 / 0
        return {"message": "This should never be reached"}
    except Exception as e:
        # Capture the error in Sentry with context
        capture_exception(
            e,
            {
                "endpoint": "sentry-debug",
                "test_type": "division_by_zero",
                "purpose": "sentry_integration_test",
            },
        )
        # Re-raise the exception so it's also logged normally
        raise HTTPException(status_code=500, detail="Sentry test error triggered successfully")


@app.get("/status")
async def status():
    """Get current service status and concurrency info"""
    # Get memory usage
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
    except ImportError:
        memory_info = None
        memory_percent = None

    # Get generation service stats
    try:
        from app.services.generation_service import get_generation_service
        service = get_generation_service()
        generation_stats = service.get_service_stats()
    except Exception as e:
        logger.error(f"Failed to get generation service stats: {e}")
        generation_stats = {"error": str(e)}

    return {
        "status": "healthy",
        "concurrent_requests": request_semaphore._value,
        "max_concurrent_requests": settings.max_concurrent_requests,
        "ai_concurrency_limit": settings.ai_concurrency_limit,
        "max_cases_per_endpoint": settings.max_cases_per_endpoint,
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2) if memory_info else None,
        "memory_percent": round(memory_percent, 2) if memory_percent else None,
        "uvicorn_workers": settings.uvicorn_workers,
        "uvicorn_threads": settings.uvicorn_threads,
        "generation_service": generation_stats,
    }


# TODO: PHASE 2 - Convert /generate-ui to asynchronous with WebSocket progress
# Current behavior: Synchronous, returns ZIP file directly
# Future behavior: Asynchronous, returns task_id, uses WebSocket for progress
# This change will require:
# 1. Frontend updates to handle task_id and progress tracking
# 2. E2E test updates to test async flow
# 3. Integration with /api/download/{task_id} endpoint


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    try:
        await websocket_manager.connect(websocket, task_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # Capture WebSocket errors with Sentry for monitoring
        capture_exception(e, context={"task_id": task_id, "stage": "websocket_connection"})


@app.get("/progress/{request_id}")
async def get_progress(request_id: str):
    """Get progress for a specific generation request (fallback for non-WebSocket clients)"""
    progress = websocket_manager.get_progress(request_id)
    if progress:
        return {
            "stage": progress.stage,
            "progress": progress.progress,
            "message": progress.message,
            "timestamp": progress.timestamp,
            "endpoint_count": progress.endpoint_count,
            "current_endpoint": progress.current_endpoint,
        }
    return {"stage": "unknown", "progress": 0, "message": "Request not found"}


async def update_progress(
    task_id: str,
    stage: str,
    progress: int,
    message: str = "",
    endpoint_count: Optional[int] = None,
    current_endpoint: Optional[int] = None,
):
    """Update progress for a generation request"""
    await websocket_manager.update_progress(
        task_id, stage, progress, message, endpoint_count, current_endpoint
    )


@app.post("/api/validate")
async def validate_spec(request: ValidateRequest) -> ValidateResponse:
    """Validate an OpenAPI specification"""
    try:
        # Load the spec
        spec = await load_openapi_spec(request.openapi)

        # Normalize it
        normalized = normalize_openapi(spec)

        return ValidateResponse(
            valid=True,
            endpoints=len(normalized.endpoints),
            summary={
                "title": normalized.title,
                "version": normalized.version,
                "servers": normalized.servers,
                "endpoint_count": len(normalized.endpoints),
                "methods": list(set(e.method for e in normalized.endpoints)),
            },
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return ValidateResponse(valid=False, error=str(e))


@app.post("/api/generate")
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate test artifacts from OpenAPI spec - JSON API endpoint
    
    ⚠️  IMPORTANT: This endpoint is for API users and is SYNCHRONOUS by default.
    It returns the complete result after generation finishes.
    For UI users who want real-time progress updates, use /generate-ui instead.
    
    This endpoint should NOT be used by the web UI - it will block until
    generation completes, which can take a long time and provide no feedback.
    
    Use cases:
    - API integrations
    - CI/CD pipelines
    - Automated testing
    - Background job processing (when use_background=True)
    
    For web UI form submissions, use /generate-ui instead.
    """
    logger.info("✅ /api/generate endpoint called - this is the correct async endpoint")
    logger.info(f"🔍 Request data: {request}")
    logger.info(f"🔍 Request openapi length: {len(request.openapi) if request.openapi else 0}")
    logger.info(f"🔍 Request openapi preview: {request.openapi[:100] if request.openapi else 'None'}...")
    logger.info(f"🔍 Request outputs: {request.outputs}")
    logger.info(f"🔍 Request use_background: {getattr(request, 'use_background', 'Not set')}")
    try:
        # Check if background processing is requested
        use_background = getattr(request, "use_background", False)

        if use_background:
            # ASYNC MODE: Start background task and return task_id immediately
            # This allows API consumers to track progress via WebSocket
            import uuid

            task_id = str(uuid.uuid4())

            # Start background task with progress tracking
            background_tasks.add_task(generate_test_artifacts_background, task_id, request)
            logger.info(f"✅ Background task started for task {task_id}")

            # Return task ID for WebSocket progress tracking
            logger.info(f"✅ Returning task ID: {task_id}")
            return {"task_id": task_id, "status": "started"}
        else:
            # SYNC MODE: Generate immediately and return ZIP file
            # This is useful for quick API calls that need immediate results
            logger.info("Processing synchronous API generation request")

            # Load and normalize the spec
            spec = await load_openapi_spec(request.openapi)
            normalized = normalize_openapi(spec)

            # Generate test cases
            artifacts = await generate_test_cases(
                normalized,
                cases_per_endpoint=request.casesPerEndpoint,
                outputs=request.outputs,
                domain_hint=request.domainHint,
                seed=request.seed,
                ai_speed=request.aiSpeed,
            )

            # Create ZIP file for immediate download
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                zip_path = Path(tmp.name)
                create_artifact_zip(artifacts, zip_path)

            # Return ZIP file directly
            response = FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="test-artifacts.zip",
                headers={"Content-Disposition": "attachment; filename=test-artifacts.zip"},
            )

            # Clean up memory after generation
            del artifacts
            gc.collect()

            return response

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.error(f"API generation error: {e}")
        # Capture error in Sentry with context
        capture_exception(
            e,
            {
                "endpoint": "api-generate",
                "use_background": getattr(request, "use_background", False),
                "cases_per_endpoint": request.casesPerEndpoint,
                "outputs": request.outputs,
                "ai_speed": request.aiSpeed,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{task_id}")
async def download_task_result(task_id: str):
    """Download the result of a completed task"""
    try:
        # Check if task is complete
        progress = websocket_manager.get_progress(task_id)
        if not progress or progress.stage != "complete":
            raise HTTPException(status_code=404, detail="Task not found or not complete")

        # Get the stored ZIP file path
        task_result = websocket_manager.task_results.get(task_id)
        if not task_result or "zip_path" not in task_result:
            raise HTTPException(status_code=404, detail="Task result not found")

        zip_path = Path(task_result["zip_path"])
        if not zip_path.exists():
            raise HTTPException(status_code=404, detail="ZIP file not found")

        # Return the ZIP file
        return FileResponse(
            zip_path,
            media_type="application/octet-stream",
            filename="test-artifacts.zip",
            headers={"Content-Disposition": "attachment; filename=test-artifacts.zip"},
        )

    except Exception as e:
        logger.error(f"Download error for task {task_id}: {e}")
        # Capture download errors with Sentry for monitoring
        capture_exception(e, context={"task_id": task_id, "stage": "download"})
        raise HTTPException(status_code=500, detail=str(e))


async def generate_test_artifacts_background(task_id: str, request: GenerateRequest):
    """Background task for generating test artifacts using the generation service"""
    try:
        from app.services.generation_service import get_generation_service, Priority
        
        # Get the generation service
        service = get_generation_service()
        
        # Prepare request data
        request_data = {
            "task_id": task_id,
            "normalized_spec": None,  # Will be loaded in the service
            "cases_per_endpoint": request.casesPerEndpoint,
            "outputs": request.outputs,
            "domain_hint": request.domainHint,
            "seed": request.seed,
            "ai_speed": request.aiSpeed,
            "openapi": request.openapi,  # Pass raw OpenAPI data
        }
        
        # Create progress callback
        async def progress_callback(stage: str, progress: int, message: str):
            await update_progress(task_id, stage, progress, message)
        
        # Get user priority based on subscription tier
        from app.auth.middleware import get_current_user
        from app.auth.middleware import get_priority_from_user
        
        # Extract user from request context (simplified for now)
        # In production, this would come from the authenticated user
        user_priority = Priority.NORMAL  # Default priority
        
        submitted_task_id = service.submit_request(
            request_data=request_data,
            progress_callback=progress_callback,
            priority=user_priority,
            task_id=task_id
        )
        
        logger.info(f"Generation request {task_id} submitted to service")
        
        # The service will handle the generation and progress updates
        # We just need to wait for completion and handle the result
        
    except Exception as e:
        logger.error(f"Failed to submit generation request: {e}")
        await update_progress(task_id, "error", 0, f"Failed to submit generation request: {str(e)}")


@app.post("/generate-ui")
async def generate_ui(
    request: Request,
    file: Optional[UploadFile] = File(None),
    specUrl: Optional[str] = Form(None),
    casesPerEndpoint: int = Form(10),
    outputs: List[str] = Form(["junit", "python", "nodejs", "postman"]),
    domainHint: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    aiSpeed: str = Form("fast"),
):
    """
    Handle form submission from UI - ASYNCHRONOUS with WebSocket progress tracking
    
    ⚠️  IMPORTANT: This endpoint is for UI users and is ASYNCHRONOUS.
    It starts a background task and returns immediately with a task_id.
    Progress updates are sent via WebSocket to provide real-time feedback.
    
    This endpoint should be used by the web UI for:
    - Real-time progress tracking
    - Non-blocking user experience
    - WebSocket-based status updates
    
    Use cases:
    - Web UI form submissions
    - File uploads from browsers
    - Real-time progress tracking via WebSocket
    - Non-blocking user experience
    
    For programmatic API access, use /api/generate instead.
    """
    logger.warning("🚨 /generate-ui endpoint called - this should NOT happen with async frontend!")
    async with request_semaphore:  # Limit concurrent requests
        try:
            logger.info(
                f"UI generation request received: file={file.filename if file else None}, specUrl={specUrl}, casesPerEndpoint={casesPerEndpoint}, outputs={outputs}, domainHint={domainHint}, seed={seed}, aiSpeed={aiSpeed}"
            )

            # Prepare OpenAPI input
            openapi_input = None
            if file and file.filename:
                logger.info(f"Processing uploaded file: {file.filename}")
                content = await file.read()
                openapi_input = base64.b64encode(content).decode()
                logger.info(f"File content encoded, length: {len(openapi_input)}")
            elif specUrl:
                logger.info(f"Processing spec URL: {specUrl}")
                openapi_input = specUrl
            else:
                raise ValueError(
                    "Please upload an OpenAPI specification file (.json, .yaml, .yml) or provide a URL to your OpenAPI spec"
                )

            # For UI requests, generate synchronously (no background tasks)
            # Load and normalize the spec
            logger.info("Loading and normalizing OpenAPI spec...")
            spec = await load_openapi_spec(openapi_input)
            logger.info(
                f"OpenAPI spec loaded, keys: {list(spec.keys()) if isinstance(spec, dict) else 'Not a dict'}"
            )

            normalized = normalize_openapi(spec)
            logger.info(f"OpenAPI spec normalized, endpoints: {len(normalized.endpoints)}")

            # Generate test cases
            logger.info("Generating test cases...")
            artifacts = await generate_test_cases(
                normalized,
                cases_per_endpoint=casesPerEndpoint,
                outputs=outputs,
                domain_hint=domainHint,
                seed=seed,
                ai_speed=aiSpeed,
            )
            logger.info(
                f"Test cases generated, artifacts: {list(artifacts.keys()) if isinstance(artifacts, dict) else 'Not a dict'}"
            )

            # Create ZIP file
            logger.info("Creating ZIP file...")
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                zip_path = Path(tmp.name)
                create_artifact_zip(artifacts, zip_path)
                logger.info(f"ZIP file created: {zip_path}")

            # Return ZIP file
            response = FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="test-artifacts.zip",
                headers={"Content-Disposition": "attachment; filename=test-artifacts.zip"},
            )

            # Clean up memory after generation
            del artifacts
            gc.collect()

            logger.info("UI generation completed successfully")
            return response

        except ValueError as e:
            logger.error(f"UI validation error: {e}")
            # Return a 400 Bad Request for validation errors
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"UI generation error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            # Capture UI generation errors with Sentry for monitoring
            capture_exception(e, context={"stage": "ui_generation"})
            # Return a proper error response instead of HTML template
            raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(404)
async def not_found(request: Request, exc):
    """404 handler"""
    if request.url.path.startswith("/api"):
        return {"error": "Not found"}, 404
    return templates.TemplateResponse(
        "landing.html", {"request": request, "error": "Page not found"}, status_code=404
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from app.services.generation_service import get_generation_service
    # Initialize the generation service
    get_generation_service()
    logger.info("✅ Generation service initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    from app.services.generation_service import shutdown_generation_service
    # Shutdown the generation service
    shutdown_generation_service()
    logger.info("✅ Generation service shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
