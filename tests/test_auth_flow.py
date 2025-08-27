"""
Test authentication flow with Selenium.

This test runs the server with authentication enabled and tests the OAuth flow
using Selenium to navigate through the authentication providers.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from test_e2e_functional import WebService


class TestAuthFlow:
    """Test authentication flow with real server and Selenium."""

    @pytest.fixture(scope="class")
    def web_service(self):
        """Start web service with authentication enabled."""
        service = WebService(enable_auth=True)
        service.start()
        yield service
        service.stop()

    @pytest.fixture(scope="class")
    def driver(self):
        """Create and configure Chrome WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        yield driver
        driver.quit()

    def test_github_oauth_flow(self, web_service, driver):
        """Test GitHub OAuth flow."""
        # Navigate to login page
        driver.get(f"http://localhost:{web_service.port}/login")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Verify we're on the login page
        assert "Authentication" in driver.title
        
        # Find and click GitHub OAuth button
        github_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue with GitHub')]")
        github_button.click()
        
        # Wait for redirect to complete
        time.sleep(2)
        
        # Should be redirected to mock success page
        assert "Authentication Success" in driver.title
        assert "github" in driver.current_url.lower()
        
        # Wait for automatic redirect to app page
        WebDriverWait(driver, 10).until(
            lambda d: "/app" in d.current_url
        )
        
        # Verify we're on the app page
        assert "Test Data Generator" in driver.title
        
        # Check that localStorage has the mock token
        token = driver.execute_script("return localStorage.getItem('clerk_token');")
        assert token is not None
        assert token.startswith("mock-jwt-github")

    def test_google_oauth_flow(self, web_service, driver):
        """Test Google OAuth flow."""
        # Navigate to login page
        driver.get(f"http://localhost:{web_service.port}/login")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Find and click Google OAuth button
        google_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue with Google')]")
        google_button.click()
        
        # Wait for redirect to complete
        time.sleep(2)
        
        # Should be redirected to mock success page
        assert "Authentication Success" in driver.title
        assert "google" in driver.current_url.lower()
        
        # Wait for automatic redirect to app page
        WebDriverWait(driver, 10).until(
            lambda d: "/app" in d.current_url
        )
        
        # Check that localStorage has the mock token
        token = driver.execute_script("return localStorage.getItem('clerk_token');")
        assert token is not None
        assert token.startswith("mock-jwt-google")

    def test_apple_oauth_flow(self, web_service, driver):
        """Test Apple OAuth flow."""
        # Navigate to login page
        driver.get(f"http://localhost:{web_service.port}/login")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Find and click Apple OAuth button
        apple_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue with Apple')]")
        apple_button.click()
        
        # Wait for redirect to complete
        time.sleep(2)
        
        # Should be redirected to mock success page
        assert "Authentication Success" in driver.title
        assert "apple" in driver.current_url.lower()
        
        # Wait for automatic redirect to app page
        WebDriverWait(driver, 10).until(
            lambda d: "/app" in d.current_url
        )
        
        # Check that localStorage has the mock token
        token = driver.execute_script("return localStorage.getItem('clerk_token');")
        assert token is not None
        assert token.startswith("mock-jwt-apple")

    def test_authenticated_access_to_protected_routes(self, web_service, driver):
        """Test that authenticated users can access protected routes."""
        # First authenticate via GitHub
        driver.get(f"http://localhost:{web_service.port}/login")
        github_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue with GitHub')]")
        github_button.click()
        
        # Wait for redirect to app page
        WebDriverWait(driver, 10).until(
            lambda d: "/app" in d.current_url
        )
        
        # Now try to access the generate endpoint directly
        driver.get(f"http://localhost:{web_service.port}/generate-ui")
        
        # Should not be redirected to login
        assert "/generate-ui" in driver.current_url
        
        # Should see the generation form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )

    def test_unauthenticated_access_redirects_to_login(self, web_service, driver):
        """Test that unauthenticated users are redirected to login."""
        # Clear any existing tokens
        driver.execute_script("localStorage.clear();")
        
        # Try to access protected route
        driver.get(f"http://localhost:{web_service.port}/app")
        
        # Should be redirected to login
        WebDriverWait(driver, 10).until(
            lambda d: "/login" in d.current_url
        )
        
        # Should see login form
        assert "Authentication" in driver.title
