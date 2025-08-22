"""FastAPI main application"""
import base64

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.schemas import GenerateRequest, ValidateRequest, ValidateResponse
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi
from app.utils.zipping import create_artifact_zip
from app.generation.cases import generate_test_cases

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
async def generate(request: GenerateRequest):
    """Generate test artifacts from OpenAPI spec"""
    try:
        # Load and normalize the spec
        spec = await load_openapi_spec(request.openapi)
        normalized = normalize_openapi(spec)

        # Generate test cases
        artifacts = await generate_test_cases(
            normalized,
            cases_per_endpoint=request.casesPerEndpoint,
            outputs=request.outputs,
            domain_hint=request.domainHint,
            seed=request.seed
        )

        # Create ZIP file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = Path(tmp.name)
            create_artifact_zip(artifacts, zip_path)

        # Return ZIP file
        return FileResponse(
            zip_path,
            media_type="application/octet-stream",
            filename="test-artifacts.zip",
            headers={
                "Content-Disposition": "attachment; filename=test-artifacts.zip"
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-ui")
async def generate_ui(
    request: Request,
    file: Optional[UploadFile] = File(None),
    specUrl: Optional[str] = Form(None),
    casesPerEndpoint: int = Form(10),
    outputs: List[str] = Form(["junit", "python", "nodejs", "postman"]),
    domainHint: Optional[str] = Form(None),
    seed: Optional[int] = Form(None)
):
    """Handle form submission from UI"""
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

        # Call generation API
        gen_request = GenerateRequest(
            openapi=openapi_input,
            casesPerEndpoint=casesPerEndpoint,
            outputs=outputs,
            domainHint=domainHint,
            seed=seed
        )

        return await generate(gen_request)

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
