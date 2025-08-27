"""
Authentication routes for user management and Clerk integration.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from app.auth.middleware import (
    get_current_user, require_auth, require_auth_or_dev, get_user_subscription, 
    get_user_usage, get_priority_from_user
)
from app.auth.clerk_auth import get_user_manager
from app.schemas import (
    AuthResponse, LoginRequest, LogoutRequest, WebhookEvent,
    UserProfile, SubscriptionTier, UsageMetrics, SUBSCRIPTION_TIERS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login with Clerk JWT token.
    
    This endpoint verifies the JWT token and creates a user session.
    """
    try:
        from app.auth.clerk_auth import get_clerk_auth
        
        clerk_auth = get_clerk_auth()
        token_payload = clerk_auth.verify_jwt(request.token)
        
        if not token_payload:
            return AuthResponse(
                authenticated=False,
                error="Invalid or expired token"
            )
        
        # Extract user information
        user_info = clerk_auth.extract_user_info(token_payload)
        user_profile = UserProfile(**user_info)
        
        # Create user session
        user_manager = get_user_manager()
        session_id = user_manager.create_session(user_profile.user_id, user_info)
        
        # Get subscription and usage information
        subscription = SUBSCRIPTION_TIERS["free"]  # TODO: Get from database
        usage = UsageMetrics(
            user_id=user_profile.user_id,
            tier=subscription.tier,
            current_period="2025-01",  # TODO: Get current billing period
            generations_used=0,
            generations_limit=subscription.limits["generations_per_month"],
            downloads_used=0,
            downloads_limit=subscription.limits["downloads_per_month"],
            endpoints_processed=0,
            storage_used_mb=0.0,
            storage_limit_mb=subscription.limits["storage_mb"]
        )
        
        logger.info(f"User {user_profile.user_id} logged in successfully")
        
        return AuthResponse(
            authenticated=True,
            user=user_profile,
            subscription=subscription,
            usage=usage,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return AuthResponse(
            authenticated=False,
            error="Login failed"
        )


@router.post("/logout", response_model=Dict[str, str])
async def logout(request: LogoutRequest):
    """
    Logout and invalidate user session.
    """
    try:
        user_manager = get_user_manager()
        # TODO: Implement session invalidation
        # For now, just return success
        
        logger.info(f"User logged out successfully")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    current_user: Optional[UserProfile] = Depends(require_auth_or_dev)
):
    """
    Get current user information, subscription, and usage.
    """
    try:
        # If in dev mode and no user, return a mock authenticated response
        if current_user is None:
            from app.config import settings
            if settings.disable_auth_for_dev:
                logger.info("🔓 Development mode: Returning mock authenticated user")
                mock_user = UserProfile(
                    user_id="dev-user",
                    email="dev@example.com",
                    first_name="Dev",
                    last_name="User",
                    image_url=""
                )
                subscription = SUBSCRIPTION_TIERS["free"]
                usage = UsageMetrics(
                    user_id="dev-user",
                    tier=subscription.tier,
                    current_period="2025-01",
                    generations_used=0,
                    generations_limit=subscription.limits["generations_per_month"],
                    downloads_used=0,
                    downloads_limit=subscription.limits["downloads_per_month"],
                    endpoints_processed=0,
                    storage_used_mb=0.0,
                    storage_limit_mb=subscription.limits["storage_mb"]
                )
                return AuthResponse(
                    authenticated=True,
                    user=mock_user,
                    subscription=subscription,
                    usage=usage
                )
        
        subscription = await get_user_subscription(current_user)
        usage = await get_user_usage(current_user)
        
        return AuthResponse(
            authenticated=True,
            user=current_user,
            subscription=subscription,
            usage=usage
        )
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")


@router.get("/subscription", response_model=SubscriptionTier)
async def get_subscription(
    current_user: UserProfile = Depends(require_auth)
):
    """
    Get user's current subscription tier.
    """
    return await get_user_subscription(current_user)


@router.get("/usage", response_model=UsageMetrics)
async def get_usage(
    current_user: UserProfile = Depends(require_auth)
):
    """
    Get user's current usage metrics.
    """
    return await get_user_usage(current_user)


@router.get("/tiers", response_model=Dict[str, SubscriptionTier])
async def get_available_tiers():
    """
    Get all available subscription tiers.
    """
    return SUBSCRIPTION_TIERS


@router.post("/webhook/clerk")
async def clerk_webhook(request: Request):
    """
    Handle Clerk webhook events.
    
    This endpoint receives webhook notifications from Clerk about user events
    like user creation, deletion, profile updates, etc.
    """
    try:
        from app.config import settings
        
        # Get the raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature
        if not _verify_webhook_signature(body, headers, settings.clerk_webhook_secret):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse the webhook event
        event_data = await request.json()
        event_type = event_data.get("type")
        event_object = event_data.get("object")
        event_data_payload = event_data.get("data", {})
        
        logger.info(f"Received Clerk webhook: {event_type}")
        logger.info(f"Event object: {event_object}")
        
        # Handle different event types
        if event_type == "user.created":
            await _handle_user_created(event_data_payload)
        elif event_type == "user.updated":
            await _handle_user_updated(event_data_payload)
        elif event_type == "user.deleted":
            await _handle_user_deleted(event_data_payload)
        elif event_type == "session.created":
            await _handle_session_created(event_data_payload)
        elif event_type == "session.revoked":
            await _handle_session_revoked(event_data_payload)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook handling error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


def _verify_webhook_signature(body: bytes, headers: dict, webhook_secret: str) -> bool:
    """
    Verify Clerk webhook signature.
    
    Args:
        body: Raw request body
        headers: Request headers
        webhook_secret: Clerk webhook signing secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        import hmac
        import hashlib
        
        # Get the signature from headers
        svix_id = headers.get("svix-id")
        svix_timestamp = headers.get("svix-timestamp")
        svix_signature = headers.get("svix-signature")
        
        if not all([svix_id, svix_timestamp, svix_signature]):
            logger.warning("Missing webhook signature headers")
            return False
        
        # Create the signed payload
        signed_payload = f"{svix_id}.{svix_timestamp}.{body.decode('utf-8')}"
        
        # Create the expected signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(f"v1,{expected_signature}", svix_signature)
        
    except Exception as e:
        logger.error(f"Webhook signature verification error: {e}")
        return False


async def _handle_user_created(data: Dict[str, Any]):
    """Handle user creation event"""
    user_id = data.get("id")
    email = data.get("email_addresses", [{}])[0].get("email_address")
    
    logger.info(f"New user created: {user_id} ({email})")
    
    # TODO: Create user record in database
    # TODO: Assign default subscription tier
    # TODO: Initialize usage tracking


async def _handle_user_updated(data: Dict[str, Any]):
    """Handle user update event"""
    user_id = data.get("id")
    logger.info(f"User updated: {user_id}")
    
    # TODO: Update user record in database


async def _handle_user_deleted(data: Dict[str, Any]):
    """Handle user deletion event"""
    user_id = data.get("id")
    logger.info(f"User deleted: {user_id}")
    
    # TODO: Clean up user data
    # TODO: Cancel subscriptions
    # TODO: Archive usage data


async def _handle_session_created(data: Dict[str, Any]):
    """Handle session creation event"""
    session_id = data.get("id")
    user_id = data.get("user_id")
    
    logger.info(f"Session created: {session_id} for user {user_id}")
    
    # TODO: Track active sessions


async def _handle_session_revoked(data: Dict[str, Any]):
    """Handle session revocation event"""
    session_id = data.get("id")
    user_id = data.get("user_id")
    
    logger.info(f"Session revoked: {session_id} for user {user_id}")
    
    # TODO: Clean up session data
