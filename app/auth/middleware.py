"""
Authentication middleware for protecting routes and extracting user information.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.clerk_auth import get_clerk_auth, get_user_manager
from app.schemas import UserProfile, SubscriptionTier, UsageMetrics, SUBSCRIPTION_TIERS

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserProfile]:
    """
    Extract and verify current user from JWT token.

    Args:
        request: FastAPI request object for accessing app state
        credentials: HTTP Bearer token credentials

    Returns:
        UserProfile if authenticated, None if no token provided

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not credentials:
        return None

    try:
        # Check if this is a mock token for testing
        if credentials.credentials.startswith("mock-jwt-"):
            if hasattr(request.app.state, "mock_users"):
                mock_user_data = request.app.state.mock_users.get(credentials.credentials)
                if mock_user_data:
                    logger.info(f"Using mock token for user: {mock_user_data['user'].user_id}")
                    return mock_user_data["user"]

            # Mock token not found or invalid
            raise HTTPException(status_code=401, detail="Invalid mock token")

        # Handle real Clerk JWT tokens
        clerk_auth = get_clerk_auth()
        token_payload = clerk_auth.verify_jwt(credentials.credentials)

        if not token_payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_info = clerk_auth.extract_user_info(token_payload)
        return UserProfile(**user_info)

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def require_auth(
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> UserProfile:
    """
    Require authentication for protected routes.

    Args:
        current_user: Current user from JWT token

    Returns:
        UserProfile if authenticated

    Raises:
        HTTPException: If not authenticated
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return current_user


async def require_auth_or_dev(
    request: Request,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Optional[UserProfile]:
    """
    Require authentication for protected routes, but allow bypass in development.

    Args:
        current_user: Current user from JWT token
        request: FastAPI request object

    Returns:
        UserProfile if authenticated, None if in dev mode

    Raises:
        HTTPException: If not authenticated and not in dev mode
    """
    from app.config import settings

    # Allow bypass in development mode
    if settings.disable_auth_for_dev:
        logger.info("🔓 Development mode: Authentication bypassed")
        return None

    if not current_user:
        # Check if this is an HTML request (browser navigation)
        if request and "text/html" in request.headers.get("accept", ""):
            from fastapi.responses import RedirectResponse

            redirect_url = f"/login?redirect={request.url.path}"
            raise HTTPException(status_code=302, detail=f"Redirect to {redirect_url}")
        else:
            raise HTTPException(status_code=401, detail="Authentication required")

    return current_user


async def get_user_subscription(
    current_user: UserProfile = Depends(require_auth),
) -> SubscriptionTier:
    """
    Get user's subscription tier.

    Args:
        current_user: Authenticated user

    Returns:
        User's subscription tier
    """
    # TODO: Implement database lookup for user subscription
    # For now, return free tier for all users
    return SUBSCRIPTION_TIERS["free"]


async def get_user_usage(current_user: UserProfile = Depends(require_auth)) -> UsageMetrics:
    """
    Get user's current usage metrics.

    Args:
        current_user: Authenticated user

    Returns:
        User's usage metrics
    """
    # TODO: Implement database lookup for usage tracking
    # For now, return default usage metrics
    subscription = await get_user_subscription(current_user)

    return UsageMetrics(
        user_id=current_user.user_id,
        tier=subscription.tier,
        current_period="2025-01",  # TODO: Get current billing period
        generations_used=0,
        generations_limit=subscription.limits["generations_per_month"],
        downloads_used=0,
        downloads_limit=subscription.limits["downloads_per_month"],
        endpoints_processed=0,
        storage_used_mb=0.0,
        storage_limit_mb=subscription.limits["storage_mb"],
    )


async def check_generation_limit(
    current_user: UserProfile = Depends(require_auth),
    user_usage: UsageMetrics = Depends(get_user_usage),
) -> bool:
    """
    Check if user can perform a generation operation.

    Args:
        current_user: Authenticated user
        user_usage: User's current usage

    Returns:
        True if generation is allowed

    Raises:
        HTTPException: If generation limit exceeded
    """
    subscription = await get_user_subscription(current_user)

    # Check generation limit
    if subscription.limits["generations_per_month"] != -1:  # Not unlimited
        if user_usage.generations_used >= subscription.limits["generations_per_month"]:
            raise HTTPException(
                status_code=429,
                detail=f"Generation limit exceeded. Upgrade to {subscription.name} tier for more generations.",
            )

    # Check endpoint limit
    if subscription.limits["max_endpoints"] != -1:  # Not unlimited
        # This would need to be checked when the OpenAPI spec is processed
        pass

    return True


async def check_download_limit(
    current_user: UserProfile = Depends(require_auth),
    user_usage: UsageMetrics = Depends(get_user_usage),
) -> bool:
    """
    Check if user can perform a download operation.

    Args:
        current_user: Authenticated user
        user_usage: User's current usage

    Returns:
        True if download is allowed

    Raises:
        HTTPException: If download limit exceeded
    """
    subscription = await get_user_subscription(current_user)

    # Check download limit
    if subscription.limits["downloads_per_month"] != -1:  # Not unlimited
        if user_usage.downloads_used >= subscription.limits["downloads_per_month"]:
            raise HTTPException(
                status_code=429,
                detail=f"Download limit exceeded. Upgrade to {subscription.name} tier for more downloads.",
            )

    return True


async def require_auth_or_free_tier(
    request: Request,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Optional[UserProfile]:
    """
    Require authentication for protected routes, but allow Free tier access without auth.

    Args:
        current_user: Current user from JWT token
        request: FastAPI request object

    Returns:
        UserProfile if authenticated, None if Free tier access

    Raises:
        HTTPException: If not authenticated and not Free tier access
    """
    from app.config import settings

    # Allow bypass in development mode
    if settings.disable_auth_for_dev:
        logger.info("🔓 Development mode: Authentication bypassed")
        return None

    # If authenticated, return user
    if current_user:
        return current_user

    # For unauthenticated users, allow Free tier access
    logger.info("🔓 Free tier access: Allowing unauthenticated access")
    return None


def get_priority_from_user(user: UserProfile) -> int:
    """
    Get generation priority based on user's subscription tier.

    Args:
        user: User profile

    Returns:
        Priority level (1=HIGH, 2=NORMAL, 3=LOW)
    """
    # TODO: Implement database lookup for user subscription
    # For now, return NORMAL priority for all users
    return 2  # NORMAL priority
