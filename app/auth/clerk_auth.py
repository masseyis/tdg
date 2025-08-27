"""
Clerk Authentication Module

Handles user authentication via Clerk JWT tokens and webhooks.
Supports GitHub, Google, Apple, and other OAuth providers.
"""

import json
import logging
import time
from typing import Dict, Optional, Any
from urllib.request import urlopen
from urllib.error import URLError
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

logger = logging.getLogger(__name__)


class ClerkAuth:
    """
    Clerk authentication handler for JWT verification and user management.
    
    Supports:
    - JWT token verification
    - User profile extraction
    - Subscription tier management
    - Usage tracking
    """
    
    def __init__(self, clerk_jwt_public_key: str, clerk_issuer: str):
        """
        Initialize Clerk authentication.
        
        Args:
            clerk_jwt_public_key: Clerk's JWT public key for verification
            clerk_issuer: Clerk issuer URL (e.g., https://clerk.your-domain.com)
        """
        self.clerk_jwt_public_key = clerk_jwt_public_key
        self.clerk_issuer = clerk_issuer.rstrip('/')
        
        # Fetch Clerk's public keys for JWT verification
        self.public_keys = self._fetch_public_keys()
        
        logger.info(f"Clerk authentication initialized for issuer: {clerk_issuer}")
    
    def _fetch_public_keys(self) -> Dict[str, Any]:
        """Fetch Clerk's public keys for JWT verification"""
        try:
            jwks_url = f"{self.clerk_issuer}/.well-known/jwks.json"
            with urlopen(jwks_url) as response:
                jwks = json.loads(response.read().decode('utf-8'))
                logger.info(f"Fetched {len(jwks.get('keys', []))} public keys from Clerk")
                return jwks
        except (URLError, json.JSONDecodeError) as e:
            logger.error(f"Failed to fetch Clerk public keys: {e}")
            return {"keys": []}
    
    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token from Clerk.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode without verification first to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get('kid')
            
            if not key_id:
                logger.error("JWT token missing key ID")
                return None
            
            # Find the corresponding public key
            public_key = None
            for key in self.public_keys.get('keys', []):
                if key.get('kid') == key_id:
                    public_key = key
                    break
            
            if not public_key:
                logger.error(f"Public key not found for key ID: {key_id}")
                return None
            
            # Convert JWK to PEM format (simplified approach)
            # In production, you might want to use a proper JWK to PEM converter
            pem_key = self._jwk_to_pem(public_key)
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                pem_key,
                algorithms=['RS256'],
                audience='your-app-audience',  # Set this to your app's audience
                issuer=self.clerk_issuer,
                options={'verify_signature': True}
            )
            
            logger.info(f"JWT token verified for user: {payload.get('sub')}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            return None
    
    def _jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        """
        Convert JWK to PEM format.
        
        This is a simplified implementation. In production,
        consider using a proper JWK to PEM converter library.
        """
        # For now, return the raw key - you may need to implement
        # proper JWK to PEM conversion based on your needs
        return jwk.get('n', '')  # This is a placeholder
    
    def extract_user_info(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from JWT token payload.
        
        Args:
            token_payload: Decoded JWT token payload
            
        Returns:
            User information dictionary
        """
        user_id = token_payload.get('sub')
        email = token_payload.get('email')
        email_verified = token_payload.get('email_verified', False)
        
        # Extract OAuth provider information
        oauth_provider = None
        if 'github' in token_payload:
            oauth_provider = 'github'
        elif 'google' in token_payload:
            oauth_provider = 'google'
        elif 'apple' in token_payload:
            oauth_provider = 'apple'
        
        return {
            'user_id': user_id,
            'email': email,
            'email_verified': email_verified,
            'oauth_provider': oauth_provider,
            'created_at': token_payload.get('iat'),
            'expires_at': token_payload.get('exp'),
        }
    
    def get_user_tier(self, user_id: str) -> str:
        """
        Get user's subscription tier.
        
        Args:
            user_id: Clerk user ID
            
        Returns:
            Subscription tier: 'free', 'basic', 'pro', 'enterprise'
        """
        # TODO: Implement database lookup for user subscription
        # For now, return 'free' tier
        return 'free'
    
    def check_usage_limits(self, user_id: str, operation: str) -> bool:
        """
        Check if user has exceeded usage limits for an operation.
        
        Args:
            user_id: Clerk user ID
            operation: Operation type (e.g., 'generation', 'download')
            
        Returns:
            True if operation is allowed, False if limit exceeded
        """
        # TODO: Implement database lookup for usage tracking
        # For now, allow all operations
        return True
    
    def record_usage(self, user_id: str, operation: str, details: Dict[str, Any]):
        """
        Record user usage for tracking and billing.
        
        Args:
            user_id: Clerk user ID
            operation: Operation type
            details: Operation details (e.g., endpoints processed, file size)
        """
        # TODO: Implement database storage for usage tracking
        logger.info(f"Usage recorded for user {user_id}: {operation} - {details}")


class UserManager:
    """
    Manages user sessions and subscription information.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, user_info: Dict[str, Any]) -> str:
        """Create a new user session"""
        session_id = f"session_{user_id}_{int(time.time())}"
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'user_info': user_info,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.active_sessions.get(session_id)
        if session:
            session['last_activity'] = time.time()
            return session
        return None
    
    def cleanup_expired_sessions(self, max_age: int = 3600):
        """Clean up expired sessions (default: 1 hour)"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session['last_activity'] > max_age
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# Global instances
clerk_auth: Optional[ClerkAuth] = None
user_manager = UserManager()


def get_clerk_auth() -> ClerkAuth:
    """Get the global Clerk authentication instance"""
    global clerk_auth
    if clerk_auth is None:
        from app.config import settings
        clerk_auth = ClerkAuth(
            clerk_jwt_public_key=settings.clerk_jwt_public_key,
            clerk_issuer=settings.clerk_issuer
        )
    return clerk_auth


def get_user_manager() -> UserManager:
    """Get the global user manager instance"""
    return user_manager
