"""FastAPI main application"""
import base64
import datetime
import gc
import logging
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import WebSocket, WebSocketDisconnect

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import json

from app.config import settings
from app.schemas import GenerateRequest, ValidateRequest, ValidateResponse
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi
from app.utils.zipping import create_artifact_zip
from app.generation.cases import generate_test_cases, generate_test_cases_with_progress

# Global semaphore to limit concurrent requests
import asyncio
request_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Test Data Generator",
    version="0.1.0",
    description="Generate test data from OpenAPI specifications"
)

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    """Render app page"""
    return templates.TemplateResponse("app.html", {"request": request})


@app.post("/app", response_class=HTMLResponse)
async def app_page_post(request: Request):
    """Handle form submission from app page"""
    return templates.TemplateResponse("app.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint"""
    return "OK"


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
    
    return {
        "status": "healthy",
        "concurrent_requests": request_semaphore._value,
        "max_concurrent_requests": settings.max_concurrent_requests,
        "ai_concurrency_limit": settings.ai_concurrency_limit,
        "max_cases_per_endpoint": settings.max_cases_per_endpoint,
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2) if memory_info else None,
        "memory_percent": round(memory_percent, 2) if memory_percent else None
    }

# Import WebSocket manager
from app.websocket_manager import websocket_manager

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
            "current_endpoint": progress.current_endpoint
        }
    return {
        "stage": "unknown",
        "progress": 0,
        "message": "Request not found"
    }

async def update_progress(task_id: str, stage: str, progress: int, message: str = "", 
                         endpoint_count: Optional[int] = None, current_endpoint: Optional[int] = None):
    """Update progress for a generation request"""
    await websocket_manager.update_progress(task_id, stage, progress, message, endpoint_count, current_endpoint)


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
                "methods": list(set(e.method for e in normalized.endpoints))
            }
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return ValidateResponse(
            valid=False,
            error=str(e)
        )


@app.post("/api/generate")
async def generate(
    request: Request,
    background_tasks: BackgroundTasks = None
):
    """Generate test artifacts from OpenAPI spec"""
    try:
        # Parse form data
        form_data = await request.form()
        
        # Extract parameters
        file = form_data.get("file")
        spec_url = form_data.get("specUrl")
        cases_per_endpoint = int(form_data.get("casesPerEndpoint", 10))
        outputs = json.loads(form_data.get("outputs", '["junit", "postman"]'))
        domain_hint = form_data.get("domainHint")
        seed = form_data.get("seed")
        ai_speed = form_data.get("aiSpeed", "fast")
        use_background = form_data.get("use_background", "false").lower() == "true"
        
        # Prepare OpenAPI input
        openapi_input = None
        if file and hasattr(file, 'filename') and file.filename:
            content = await file.read()
            openapi_input = base64.b64encode(content).decode()
        elif spec_url:
            openapi_input = spec_url
        else:
            raise ValueError("Please upload an OpenAPI specification file or provide a URL")
        
        # Create request object
        generate_request = GenerateRequest(
            openapi=openapi_input,
            casesPerEndpoint=cases_per_endpoint,
            outputs=outputs,
            domainHint=domain_hint,
            seed=int(seed) if seed else None,
            aiSpeed=ai_speed
        )
        
        # Check if background processing is requested
        if use_background:
            # Generate unique request ID for progress tracking
            import uuid
            task_id = str(uuid.uuid4())
            
            # Start background task
            background_tasks.add_task(
                generate_test_artifacts_background,
                task_id,
                generate_request
            )
            
            # Return task ID immediately
            return {"task_id": task_id, "status": "started"}
        else:
            # Synchronous generation (for direct API calls)
            # Load and normalize the spec
            spec = await load_openapi_spec(generate_request.openapi)
            normalized = normalize_openapi(spec)

            # Generate test cases
            artifacts = await generate_test_cases(
                normalized,
                cases_per_endpoint=generate_request.casesPerEndpoint,
                outputs=generate_request.outputs,
                domain_hint=generate_request.domainHint,
                seed=generate_request.seed,
                ai_speed=generate_request.aiSpeed
            )

            # Create ZIP file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                zip_path = Path(tmp.name)
                create_artifact_zip(artifacts, zip_path)

            # Return ZIP file
            response = FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="test-artifacts.zip",
                headers={
                    "Content-Disposition": "attachment; filename=test-artifacts.zip"
                }
            )
            
            # Clean up memory after generation
            del artifacts
            gc.collect()
            
            return response

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{task_id}")
async def download_task_result(task_id: str):
    """Download the result of a completed task"""
    try:
        # Check if task is complete
        progress = websocket_manager.get_progress(task_id)
        if not progress or progress.stage != "complete":
            raise HTTPException(status_code=404, detail="Task not found or not complete")
        
        # For now, we'll need to regenerate the file since we don't store it
        # In a production system, you'd store the file path or content
        # For now, return an error suggesting to use the synchronous endpoint
        raise HTTPException(
            status_code=501, 
            detail="Download endpoint not yet implemented. Use synchronous generation for now."
        )
        
    except Exception as e:
        logger.error(f"Download error for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_test_artifacts_background(task_id: str, request: GenerateRequest):
    """Background task for generating test artifacts"""
    try:
        await update_progress(task_id, "parsing", 10, "Parsing OpenAPI specification...")
        
        # Load and normalize the spec
        spec = await load_openapi_spec(request.openapi)
        normalized = normalize_openapi(spec)
        
        await update_progress(task_id, "parsing", 100, "OpenAPI specification parsed successfully")
        await update_progress(task_id, "generating", 20, f"Generating test cases for {len(normalized.endpoints)} endpoints...")

        # Generate test cases with detailed progress
        await update_progress(task_id, "generating", 30, "Starting AI generation...")
        artifacts = await generate_test_cases_with_progress(
            task_id,
            normalized,
            cases_per_endpoint=request.casesPerEndpoint,
            outputs=request.outputs,
            domain_hint=request.domainHint,
            seed=request.seed,
            ai_speed=request.aiSpeed
        )
        
        await update_progress(task_id, "generating", 100, "Test cases generated successfully")
        await update_progress(task_id, "zipping", 20, "Creating ZIP file...")

        # Create ZIP file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = Path(tmp.name)
            create_artifact_zip(artifacts, zip_path)
        
        await update_progress(task_id, "zipping", 100, "ZIP file created successfully")
        await update_progress(task_id, "complete", 100, "Generation complete! ZIP file ready for download.")
        
        # Store the result for later retrieval
        # Note: In a production system, you'd store this in Redis/database
        # For now, we'll just mark it as complete
        
        # Clean up memory after generation
        del artifacts
        gc.collect()
        
    except Exception as e:
        logger.error(f"Background generation error: {e}")
        await update_progress(task_id, "error", 0, f"Generation failed: {str(e)}")
    finally:
        # Clean up task data after a delay
        await asyncio.sleep(300)  # Keep for 5 minutes
        websocket_manager.cleanup_task(task_id)


@app.post("/generate-ui")
async def generate_ui(
    request: Request,
    file: Optional[UploadFile] = File(None),
    specUrl: Optional[str] = Form(None),
    casesPerEndpoint: int = Form(10),
    outputs: List[str] = Form(["junit", "python", "nodejs", "postman"]),
    domainHint: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    aiSpeed: str = Form("fast")
):
    """Handle form submission from UI"""
    async with request_semaphore:  # Limit concurrent requests
        try:
            # Prepare OpenAPI input
            openapi_input = None
            if file and file.filename:
                content = await file.read()
                openapi_input = base64.b64encode(content).decode()
            elif specUrl:
                openapi_input = specUrl
            else:
                raise ValueError("Please upload an OpenAPI specification file (.json, .yaml, .yml) or provide a URL to your OpenAPI spec")

            # For UI requests, generate synchronously (no background tasks)
            # Load and normalize the spec
            spec = await load_openapi_spec(openapi_input)
            normalized = normalize_openapi(spec)

            # Generate test cases
            artifacts = await generate_test_cases(
                normalized,
                cases_per_endpoint=casesPerEndpoint,
                outputs=outputs,
                domain_hint=domainHint,
                seed=seed,
                ai_speed=aiSpeed
            )

            # Create ZIP file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                zip_path = Path(tmp.name)
                create_artifact_zip(artifacts, zip_path)

            # Return ZIP file
            response = FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="test-artifacts.zip",
                headers={
                    "Content-Disposition": "attachment; filename=test-artifacts.zip"
                }
            )
            
            # Clean up memory after generation
            del artifacts
            gc.collect()
            
            return response

        except ValueError as e:
            logger.error(f"UI validation error: {e}")
            # Return a 400 Bad Request for validation errors
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"UI generation error: {e}")
            # Return a proper error response instead of HTML template
            raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(404)
async def not_found(request: Request, exc):
    """404 handler"""
    if request.url.path.startswith("/api"):
        return {"error": "Not found"}, 404
    return templates.TemplateResponse(
        "landing.html",
        {"request": request, "error": "Page not found"},
        status_code=404
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
