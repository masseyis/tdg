"""Pydantic schemas for request/response"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class GenerateRequest(BaseModel):
    """Request to generate test data"""

    openapi: str = Field(..., description="Base64 encoded spec content or URL")
    casesPerEndpoint: int = Field(10, ge=1, le=500)
    outputs: List[str] = Field(
        default=["junit", "python", "nodejs", "postman"],
        description="Output formats: junit, python, nodejs, postman, wiremock, json, csv, sql",
    )
    domainHint: Optional[str] = Field(None, description="Domain context hint")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    aiSpeed: str = Field("fast", description="AI generation speed: fast, balanced, quality")

    @validator("outputs")
    def validate_outputs(cls, v):
        valid = {"junit", "python", "nodejs", "postman", "wiremock", "json", "csv", "sql"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Invalid outputs: {invalid}")
        return v


class ValidateRequest(BaseModel):
    """Request to validate OpenAPI spec"""

    openapi: str = Field(..., description="Base64 encoded spec content or URL")


class ValidateResponse(BaseModel):
    """Validation response"""

    valid: bool
    endpoints: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
