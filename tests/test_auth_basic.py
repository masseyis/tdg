"""
Basic authentication tests that don't require Selenium or complex server setup.

These tests verify that the authentication endpoints are working correctly.
"""

import pytest
import httpx
import asyncio


@pytest.mark.asyncio
async def test_github_oauth_redirect():
    """Test that GitHub OAuth redirects to mock success page."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/auth/github", follow_redirects=True)
        
        assert response.status_code == 200
        assert "Authentication Success" in response.text
        assert "github" in response.text.lower()
        assert "mock-jwt-github" in response.text


@pytest.mark.asyncio
async def test_google_oauth_redirect():
    """Test that Google OAuth redirects to mock success page."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/auth/google", follow_redirects=True)
        
        assert response.status_code == 200
        assert "Authentication Success" in response.text
        assert "google" in response.text.lower()
        assert "mock-jwt-google" in response.text


@pytest.mark.asyncio
async def test_apple_oauth_redirect():
    """Test that Apple OAuth redirects to mock success page."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/auth/apple", follow_redirects=True)
        
        assert response.status_code == 200
        assert "Authentication Success" in response.text
        assert "apple" in response.text.lower()
        assert "mock-jwt-apple" in response.text


@pytest.mark.asyncio
async def test_mock_success_page():
    """Test that the mock success page works correctly."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/auth/mock-success?provider=test")
        
        assert response.status_code == 200
        assert "Authentication Success" in response.text
        assert "test" in response.text.lower()
        assert "localStorage.setItem" in response.text
        assert "mock-jwt-test" in response.text


@pytest.mark.asyncio
async def test_login_page_accessible():
    """Test that the login page is accessible."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/login")
        
        assert response.status_code == 200
        assert "Authentication" in response.text
        assert "Continue with GitHub" in response.text
        assert "Continue with Google" in response.text
        assert "Continue with Apple" in response.text


@pytest.mark.asyncio
async def test_app_page_requires_auth():
    """Test that the app page requires authentication."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/app")
        
        # Should be accessible but show authentication check
        assert response.status_code == 200
        assert "authentication" in response.text.lower()


def test_auth_endpoints_exist():
    """Test that all auth endpoints exist and respond."""
    # This test runs synchronously to check basic endpoint availability
    with httpx.Client() as client:
        # Test OAuth endpoints - FastAPI uses 307 for redirects
        response = client.get("http://localhost:8000/auth/github", follow_redirects=False)
        assert response.status_code == 307  # FastAPI uses 307 for redirects
        
        response = client.get("http://localhost:8000/auth/google", follow_redirects=False)
        assert response.status_code == 307  # FastAPI uses 307 for redirects
        
        response = client.get("http://localhost:8000/auth/apple", follow_redirects=False)
        assert response.status_code == 307  # FastAPI uses 307 for redirects
        
        # Test mock success page
        response = client.get("http://localhost:8000/auth/mock-success?provider=test")
        assert response.status_code == 200

