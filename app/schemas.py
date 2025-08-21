"""Pydantic schemas for request/response"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class GenerateRequest(BaseModel):
    """Request to generate test data"""
    openapi: str = Field(..., description="Base64 encoded spec content or URL")
    casesPerEndpoint: int = Field(10, ge=1, le=100)
    outputs: List[str] = Field(
        default=["junit", "postman", "json"],
        description="Output formats: junit, postman, wiremock, json, csv, sql"
    )
    domainHint: Optional[str] = Field(None, description="Domain context hint")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    @validator("outputs")

    def validate_outputs(cls, v):
        valid = {"junit", "postman", "wiremock", "json", "csv", "sql"}
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
