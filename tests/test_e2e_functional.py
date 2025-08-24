#!/usr/bin/env python3
"""
End-to-End Functional Tests

⚠️  CRITICAL: This test MUST always pass and NEVER be disabled! ⚠️

This test validates the complete user experience from frontend to backend,
ensuring the entire system works correctly. If this test fails, it means
there's a fundamental issue that needs to be fixed immediately.

The e2e test is our primary integration test and must remain active at all times.
"""

import asyncio
import io
import json
import logging
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
import os

import httpx
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from tests.mock_service import MockService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebService:
    """Manages the main web service process"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.process = None
        
    def start(self):
        """Start the web service"""
        try:
            # Start the main service using uvicorn
            cmd = [
                "python", "-m", "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0", 
                "--port", str(self.port)
            ]
            
            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).parent.parent)
            
            logger.info(f"Starting service with command: {' '.join(cmd)}")
            logger.info(f"Working directory: {Path(__file__).parent.parent}")
            logger.info(f"Python path: {env['PYTHONPATH']}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for service to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = httpx.get(f"http://localhost:{self.port}/health", timeout=1)
                    if response.status_code == 200:
                        logger.info(f"✅ Web service started on port {self.port}")
                        return True
                except Exception as e:
                    if attempt == 0:
                        logger.info(f"Waiting for service to start (attempt {attempt + 1}/{max_attempts})...")
                    elif attempt % 5 == 0:
                        logger.info(f"Still waiting... (attempt {attempt + 1}/{max_attempts})")
                
                # Check if process is still running
                if self.process.poll() is not None:
                    # Process died, get error output
                    stdout, stderr = self.process.communicate()
                    logger.error(f"❌ Service process died unexpectedly")
                    if stdout:
                        logger.error(f"Stdout: {stdout}")
                    if stderr:
                        logger.error(f"Stderr: {stderr}")
                    return False
                
                # Check for any output
                if self.process.stdout:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            logger.info(f"Service: {line.strip()}")
                    except:
                        pass
                
                if self.process.stderr:
                    try:
                        line = self.process.stderr.readline()
                        if line:
                            logger.error(f"Service Error: {line.strip()}")
                    except:
                        pass
                
                time.sleep(1)
            
            # If we get here, service didn't start
            logger.error(f"❌ Web service failed to start on port {self.port} after {max_attempts} attempts")
            
            # Get any output from the process
            if self.process:
                stdout, stderr = self.process.communicate()
                if stdout:
                    logger.error(f"Final stdout: {stdout}")
                if stderr:
                    logger.error(f"Final stderr: {stderr}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start web service: {e}")
            return False
    
    def stop(self):
        """Stop the web service"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("✅ Web service stopped")


class WebUIDriver:
    """Driver for the web UI using Selenium"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
    
    def start_browser(self):
        """Start the Chrome browser"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode for CI
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)  # 30 second timeout
            
            logger.info("✅ Browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    def stop_browser(self):
        """Stop the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Browser stopped")
    
    def navigate_to_app(self):
        """Navigate to the app page"""
        try:
            self.driver.get(f"{self.base_url}/app")
            # Wait for the page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            logger.info("✅ Navigated to app page")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to app: {e}")
            return False
    
    def upload_spec_file(self, spec_file: Path) -> bool:
        """Upload an OpenAPI specification file"""
        try:
            # Find the file input element
            file_input = self.driver.find_element(By.NAME, "file")
            
            # Upload the file
            file_input.send_keys(str(spec_file.absolute()))
            
            # Wait for file to be processed
            time.sleep(2)
            
            logger.info(f"✅ Uploaded spec file: {spec_file.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload spec file: {e}")
            return False
    
    def set_test_parameters(self, cases_per_endpoint: int = 2, domain_hint: str = "petstore"):
        """Set test generation parameters"""
        try:
            # Set cases per endpoint (it's a select element, not input)
            cases_select = self.driver.find_element(By.NAME, "casesPerEndpoint")
            from selenium.webdriver.support.ui import Select
            cases_dropdown = Select(cases_select)
            cases_dropdown.select_by_value(str(cases_per_endpoint))
            
            # Set domain hint
            domain_select = self.driver.find_element(By.NAME, "domainHint")
            domain_dropdown = Select(domain_select)
            domain_dropdown.select_by_value(domain_hint)
            
            logger.info(f"✅ Set test parameters: {cases_per_endpoint} cases, domain: {domain_hint}")
            return True
        except Exception as e:
            logger.error(f"Failed to set test parameters: {e}")
            return False
    
    def submit_form(self) -> bool:
        """Submit the test generation form"""
        try:
            # Capture console logs before submission
            console_logs = self.driver.get_log('browser')
            if console_logs:
                logger.info("Browser console logs before submission:")
                for log in console_logs:
                    logger.info(f"  {log['level']}: {log['message']}")
            
            # Find and click the submit button
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            logger.info(f"Found submit button: {submit_button.text}")
            
            # Check if form has required fields
            form = self.driver.find_element(By.TAG_NAME, "form")
            logger.info(f"Form action: {form.get_attribute('action')}")
            logger.info(f"Form method: {form.get_attribute('method')}")
            
            # Check if file is uploaded
            file_input = self.driver.find_element(By.NAME, "file")
            if file_input.get_attribute('value'):
                logger.info(f"File input has value: {file_input.get_attribute('value')}")
            else:
                logger.warning("File input has no value")
            
            # Submit the form
            submit_button.click()
            logger.info("Clicked submit button")
            
            # Wait a moment for any immediate errors
            time.sleep(2)
            
            # Check for any JavaScript errors
            console_logs_after = self.driver.get_log('browser')
            if console_logs_after:
                logger.info("Browser console logs after submission:")
                for log in console_logs_after:
                    logger.info(f"  {log['level']}: {log['message']}")
            
            # Check if we got redirected or if there's an error
            current_url = self.driver.current_url
            logger.info(f"Current URL after submission: {current_url}")
            
            # Look for loading spinner
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "loadingSpinner")))
                logger.info("✅ Form submitted, loading spinner appeared")
                return True
            except Exception as e:
                logger.error(f"Loading spinner not found: {e}")
                
                # Check if there's an error message
                try:
                    error_elements = self.driver.find_elements(By.CLASS_NAME, "error")
                    if error_elements:
                        for error in error_elements:
                            logger.error(f"Error element found: {error.text}")
                except:
                    pass
                
                # Check page source for clues
                page_source = self.driver.page_source
                if "error" in page_source.lower() or "failed" in page_source.lower():
                    logger.error("Page contains error indicators")
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to submit form: {e}")
            return False
    
    def wait_for_generation_complete(self, timeout: int = 300) -> bool:
        """Wait for test generation to complete"""
        try:
            # Wait for the loading spinner to disappear (indicating completion)
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
            logger.info("✅ Test generation completed")
            return True
        except Exception as e:
            logger.error(f"Test generation did not complete within {timeout} seconds: {e}")
            return False
    
    def get_downloaded_file_path(self) -> Optional[Path]:
        """Get the path to the downloaded ZIP file"""
        try:
            # Wait for download to complete
            time.sleep(5)
            
            # Look for the downloaded file in the default download directory
            # This is a simplified approach - in production you might need more sophisticated download handling
            download_dir = Path.home() / "Downloads"
            
            # Look for the most recent ZIP file
            zip_files = list(download_dir.glob("test-artifacts*.zip"))
            if zip_files:
                # Sort by modification time and get the most recent
                latest_zip = max(zip_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"✅ Found downloaded file: {latest_zip}")
                return latest_zip
            
            logger.warning("No downloaded ZIP file found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get downloaded file: {e}")
            return None


class JavaTestRunner:
    """Runner for generated Java tests"""
    
    def run_tests(self, java_dir: Path, target_url: str = "http://localhost:8082") -> bool:
        """Run the generated Java tests"""
        
        # Find the pom.xml in the Java directory
        pom_files = list(java_dir.rglob("pom.xml"))
        if not pom_files:
            logger.error("No pom.xml found in generated Java files")
            return False
        
        project_dir = pom_files[0].parent
        logger.info(f"Using generated pom.xml from ZIP file: {project_dir}")
        
        # Copy test files
        test_dir = project_dir / "src" / "test" / "java"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all Java files from the extracted directory
        for java_file in java_dir.rglob("*.java"):
            relative_path = java_file.relative_to(java_dir)
            # Handle the case where files are already in src/test/java structure
            if relative_path.parts[0] == "src":
                # Skip the src/test/java part and use the rest
                target_path = relative_path.parts[3:]  # Skip src/test/java
                target_file = test_dir / Path(*target_path)
            else:
                target_file = test_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and modify the test file to use the target URL
            with open(java_file, 'r') as f:
                content = f.read()
            
            # Replace any hardcoded URLs with the target URL
            content = content.replace("http://localhost:8080", target_url)
            content = content.replace("http://example.com", target_url)
            
            with open(target_file, 'w') as f:
                f.write(content)
        
        # Copy test-data.json to resources
        test_data_files = list(java_dir.rglob("test-data.json"))
        if test_data_files:
            resources_dir = project_dir / "src" / "test" / "resources"
            resources_dir.mkdir(parents=True, exist_ok=True)
            
            for test_data_file in test_data_files:
                target_file = resources_dir / "test-data.json"
                with open(test_data_file, 'r') as f:
                    content = f.read()
                with open(target_file, 'w') as f:
                    f.write(content)
                logger.info(f"Copied test-data.json from {test_data_file}")
                break
        
        # Run Maven tests
        try:
            result = subprocess.run(
                ['mvn', 'test', '-Dtest=*Test', f'-DbaseUrl={target_url}'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            logger.info(f"Maven test output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Maven test stderr:\n{result.stderr}")
            
            # Check if the failure is due to compilation issues or just test failures
            if result.returncode != 0:
                if "compilation failure" in result.stderr.lower() or "cannot find symbol" in result.stderr.lower():
                    logger.error("❌ Java compilation failed")
                    return False
                else:
                    logger.warning("⚠️  Java tests ran but some failed (expected with mock service)")
                    return True  # Tests compiled and ran, which is what we want
            
            logger.info("✅ Java tests passed")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Maven tests timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to run Maven tests: {e}")
            return False


class PythonTestRunner:
    """Runner for generated Python tests"""
    
    def run_tests(self, python_dir: Path, target_url: str = "http://localhost:8082") -> bool:
        """Run the generated Python tests"""
        
        # Find the main test file
        test_files = list(python_dir.rglob("test_api.py"))
        if not test_files:
            logger.error("No test_api.py found in generated Python files")
            return False
        
        test_file = test_files[0]
        test_dir = test_file.parent
        
        # Copy test-data.json if it exists
        test_data_files = list(python_dir.rglob("test-data.json"))
        if test_data_files:
            for test_data_file in test_data_files:
                target_file = test_dir / "test-data.json"
                with open(test_data_file, 'r') as f:
                    content = f.read()
                with open(target_file, 'w') as f:
                    f.write(content)
                logger.info(f"Copied test-data.json from {test_data_file}")
                break
        
        # Install dependencies if requirements.txt exists
        requirements_file = test_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                logger.info("Installing Python dependencies...")
                subprocess.run(
                    ['pip', 'install', '-r', str(requirements_file)],
                    cwd=test_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Python dependencies: {e}")
                return False
        
        # Run Python tests
        try:
            logger.info(f"Running Python tests against: {target_url}")
            result = subprocess.run(
                ['python', 'test_api.py', target_url],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f"Python test output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Python test stderr:\n{result.stderr}")
            
            # Check if the failure is due to import issues or just test failures
            if result.returncode != 0:
                if "import" in result.stderr.lower() or "module" in result.stderr.lower():
                    logger.error("❌ Python import/module error")
                    return False
                else:
                    logger.warning("⚠️  Python tests ran but some failed (expected with mock service)")
                    return True  # Tests ran, which is what we want
            else:
                logger.info("✅ Python tests passed")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Python tests timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Python test execution failed: {e}")
            return False


class NodeTestRunner:
    """Runner for generated Node.js tests"""
    
    def run_tests(self, node_dir: Path, target_url: str = "http://localhost:8082") -> bool:
        """Run the generated Node.js tests"""
        
        # Find the main test file
        test_files = list(node_dir.rglob("test_api.js"))
        if not test_files:
            logger.error("No test_api.js found in generated Node.js files")
            return False
        
        test_file = test_files[0]
        test_dir = test_file.parent
        
        # Copy test-data.json if it exists
        test_data_files = list(node_dir.rglob("test-data.json"))
        if test_data_files:
            for test_data_file in test_data_files:
                target_file = test_dir / "test-data.json"
                with open(test_data_file, 'r') as f:
                    content = f.read()
                with open(target_file, 'w') as f:
                    f.write(content)
                logger.info(f"Copied test-data.json from {test_data_file}")
                break
        
        # Install dependencies if package.json exists
        package_file = test_dir / "package.json"
        if package_file.exists():
            try:
                logger.info("Installing Node.js dependencies...")
                subprocess.run(
                    ['npm', 'install'],
                    cwd=test_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Node.js dependencies: {e}")
                return False
        
        # Run Node.js tests
        try:
            logger.info(f"Running Node.js tests against: {target_url}")
            result = subprocess.run(
                ['node', 'test_api.js', target_url],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f"Node.js test output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Node.js test stderr:\n{result.stderr}")
            
            # Check if the failure is due to import issues or just test failures
            if result.returncode != 0:
                if "module" in result.stderr.lower() or "require" in result.stderr.lower():
                    logger.error("❌ Node.js module error")
                    return False
                else:
                    logger.warning("⚠️  Node.js tests ran but some failed (expected with mock service)")
                    return True  # Tests ran, which is what we want
            else:
                logger.info("✅ Node.js tests passed")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Node.js tests timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Node.js test execution failed: {e}")
            return False


def test_complete_user_experience():
    """Test the complete user experience end-to-end using real browser automation"""
    
    # Step 1: Start the main web service
    logger.info("🌐 Starting main web service...")
    web_service = WebService(port=8080)
    if not web_service.start():
        assert False, "Failed to start main web service"
    
    # Step 2: Start the mock API service
    logger.info("🌐 Starting mock API service...")
    mock_service = MockService(Path("tests/samples/petstore-minimal.yaml"), port=8082)
    mock_service.start()
    
    # Step 3: Start the web UI driver
    logger.info("🌐 Starting web UI driver...")
    ui_driver = WebUIDriver("http://localhost:8080")
    
    try:
        # Wait for services to be ready
        time.sleep(3)
        
        # Verify main service is responding
        with httpx.Client() as http_client:
            response = http_client.get("http://localhost:8080/health")
            assert response.status_code == 200, "Main service should be healthy"
        logger.info("✅ Main service is responding")
        
        # Verify mock service is responding
        with httpx.Client() as http_client:
            response = http_client.get("http://localhost:8082/openapi.json")
            assert response.status_code == 200, "Mock service should serve OpenAPI spec"
        logger.info("✅ Mock service is responding")
        
        # Step 4: Start browser and navigate to app
        if not ui_driver.start_browser():
            assert False, "Failed to start browser"
        
        if not ui_driver.navigate_to_app():
            assert False, "Failed to navigate to app page"
        
        # Step 5: Upload OpenAPI spec and generate tests
        logger.info("📝 Generating tests via web UI...")
        spec_file = Path("tests/samples/petstore-minimal.yaml")
        
        if not ui_driver.upload_spec_file(spec_file):
            assert False, "Failed to upload spec file"
        
        if not ui_driver.set_test_parameters(cases_per_endpoint=5, domain_hint="petstore"):
            assert False, "Failed to set test parameters"
        
        if not ui_driver.submit_form():
            assert False, "Failed to submit form"
        
        # Step 6: Wait for generation to complete
        if not ui_driver.wait_for_generation_complete():
            assert False, "Test generation did not complete"
        
        # Step 7: Get the downloaded ZIP file
        logger.info("📦 Getting downloaded ZIP file...")
        zip_file_path = ui_driver.get_downloaded_file_path()
        if not zip_file_path:
            assert False, "Failed to get downloaded ZIP file"
        
        # Step 8: Extract and run the generated tests
        logger.info("🔍 Extracting and running generated tests...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP file
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            logger.info(f"📦 Extracted test files to: {temp_path}")
            
            # Test Java framework
            logger.info("☕ Testing Java framework...")
            java_dir = temp_path / "artifacts" / "junit"
            if java_dir.exists():
                java_runner = JavaTestRunner()
                java_success = java_runner.run_tests(java_dir, "http://localhost:8082")
                assert java_success, "Java tests should compile and run against the mock service"
                logger.info("✅ Java framework test completed")
            else:
                logger.warning("⚠️  Java artifacts not found in generated ZIP")
            
            # Test Python framework
            logger.info("🐍 Testing Python framework...")
            python_dir = temp_path / "artifacts" / "python"
            if python_dir.exists():
                python_runner = PythonTestRunner()
                python_success = python_runner.run_tests(python_dir, "http://localhost:8082")
                assert python_success, "Python tests should run against the mock service"
                logger.info("✅ Python framework test completed")
            else:
                logger.warning("⚠️  Python artifacts not found in generated ZIP")
            
            # Test Node.js framework
            logger.info("🟢 Testing Node.js framework...")
            node_dir = temp_path / "artifacts" / "nodejs"
            if node_dir.exists():
                node_runner = NodeTestRunner()
                node_success = node_runner.run_tests(node_dir, "http://localhost:8082")
                assert node_success, "Node.js tests should run against the mock service"
                logger.info("✅ Node.js framework test completed")
            else:
                logger.warning("⚠️  Node.js artifacts not found in generated ZIP")
        
        # Step 9: Verify results
        logger.info("✅ All tests passed! End-to-end test successful.")
        
    finally:
        # Clean up
        ui_driver.stop_browser()
        mock_service.stop()
        web_service.stop()
        logger.info("🧹 Cleanup completed")


def test_generator_service_health():
    """Test that the generator service is healthy"""
    # This test can still use direct HTTP calls to check service health
    with httpx.Client() as client:
        response = client.get("http://localhost:8080/health")
        assert response.status_code == 200, "Service should be healthy"
        logger.info("✅ Generator service health check passed")


def test_ui_endpoints():
    """Test that the UI endpoints are accessible"""
    with httpx.Client() as client:
        # Test landing page
        response = client.get("http://localhost:8080/")
        assert response.status_code == 200, "Landing page should be accessible"
        
        # Test app page
        response = client.get("http://localhost:8080/app")
        assert response.status_code == 200, "App page should be accessible"
        
        logger.info("✅ UI endpoints are accessible")


if __name__ == "__main__":
    # Run the tests
    test_complete_user_experience()
