"""
Pydantic schemas for request/response validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ValidateRequest(BaseModel):
    """Request schema for OpenAPI validation"""

    openapi: str = Field(..., description="OpenAPI specification content or URL")


class ValidateResponse(BaseModel):
    """Response schema for OpenAPI validation"""

    valid: bool
    endpoints: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GenerateRequest(BaseModel):
    """Request schema for test generation"""

    openapi: str = Field(..., description="OpenAPI specification content or URL")
    casesPerEndpoint: int = Field(10, description="Number of test cases per endpoint")
    outputs: List[str] = Field(
        ["junit", "python", "nodejs", "postman"], description="Output formats to generate"
    )
    domainHint: Optional[str] = Field(None, description="Domain hint for test data")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    aiSpeed: str = Field("fast", description="AI generation speed preference")
    use_background: Optional[bool] = Field(False, description="Use background processing")


class UserProfile(BaseModel):
    """User profile information from Clerk"""

    user_id: str
    email: Optional[str] = None
    email_verified: bool = False
    oauth_provider: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[int] = None


class SubscriptionTier(BaseModel):
    """User subscription tier information"""

    tier: str = Field(..., description="Subscription tier: free, basic, pro, enterprise")
    name: str = Field(..., description="Human-readable tier name")
    monthly_price: Optional[float] = Field(None, description="Monthly price in USD")
    features: List[str] = Field(..., description="List of features included")
    limits: Dict[str, Any] = Field(..., description="Usage limits for this tier")
    priority: int = Field(..., description="Priority level for generation queue")


class UsageMetrics(BaseModel):
    """User usage metrics"""

    user_id: str
    tier: str
    current_period: str  # e.g., "2025-01"
    generations_used: int = 0
    generations_limit: int
    downloads_used: int = 0
    downloads_limit: int
    endpoints_processed: int = 0
    storage_used_mb: float = 0.0
    storage_limit_mb: float


class AuthResponse(BaseModel):
    """Authentication response"""

    authenticated: bool
    user: Optional[UserProfile] = None
    subscription: Optional[SubscriptionTier] = None
    usage: Optional[UsageMetrics] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request (for Clerk webhook handling)"""

    token: str = Field(..., description="Clerk JWT token")


class LogoutRequest(BaseModel):
    """Logout request"""

    session_id: str = Field(..., description="Session ID to invalidate")


class WebhookEvent(BaseModel):
    """Clerk webhook event"""

    type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    object: str = Field(..., description="Object type")
    created_at: int = Field(..., description="Event timestamp")


# Subscription tier definitions
SUBSCRIPTION_TIERS = {
    "free": SubscriptionTier(
        tier="free",
        name="Free",
        monthly_price=0.0,
        features=[
            "Unlimited generations",
            "Basic test cases",
            "Standard priority",
            "Community support",
        ],
        limits={
            "generations_per_month": -1,  # Unlimited
            "downloads_per_month": 10,
            "max_endpoints": 20,
            "max_cases_per_endpoint": 5,
            "storage_mb": 100,
        },
        priority=3,  # LOW priority
    ),
    "basic": SubscriptionTier(
        tier="basic",
        name="Basic",
        monthly_price=9.99,
        features=[
            "50 generations per month",
            "Enhanced test cases",
            "Normal priority",
            "Email support",
        ],
        limits={
            "generations_per_month": 50,
            "downloads_per_month": 100,
            "max_endpoints": 100,
            "max_cases_per_endpoint": 10,
            "storage_mb": 500,
        },
        priority=2,  # NORMAL priority
    ),
    "pro": SubscriptionTier(
        tier="pro",
        name="Professional",
        monthly_price=29.99,
        features=[
            "Unlimited generations",
            "Advanced test cases",
            "High priority",
            "Priority support",
            "Custom domains",
        ],
        limits={
            "generations_per_month": -1,  # Unlimited
            "downloads_per_month": -1,  # Unlimited
            "max_endpoints": -1,  # Unlimited
            "max_cases_per_endpoint": 20,
            "storage_mb": 2000,
        },
        priority=1,  # HIGH priority
    ),
    "enterprise": SubscriptionTier(
        tier="enterprise",
        name="Enterprise",
        monthly_price=99.99,
        features=[
            "Unlimited everything",
            "Custom test case generation",
            "Highest priority",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantees",
        ],
        limits={
            "generations_per_month": -1,  # Unlimited
            "downloads_per_month": -1,  # Unlimited
            "max_endpoints": -1,  # Unlimited
            "max_cases_per_endpoint": -1,  # Unlimited
            "storage_mb": 10000,
        },
        priority=1,  # HIGH priority
    ),
}
