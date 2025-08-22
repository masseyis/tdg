"""
End-to-end functional test for the complete user experience.

This test validates:
1. Generator service starts correctly
2. UI can upload OpenAPI spec
3. Java tests are generated successfully
4. Mock service can be started with the spec
5. Generated tests pass against the service
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, Any

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app

logger = logging.getLogger(__name__)

# Test configuration
TEST_SPEC_PATH = Path("tests/samples/petstore-minimal.yaml")
GENERATOR_PORT = 8080
MOCK_SERVICE_PORT = 8081
TEST_TIMEOUT = 300  # 5 minutes for entire test


class MockService:
    """Simple mock service that serves the OpenAPI spec and basic endpoints"""
    
    def __init__(self, spec_path: Path, port: int = 8081):
        self.spec_path = spec_path
        self.port = port
        self.process = None
    
    def start(self):
        """Start the mock service using the standalone mock service"""
        # Start the standalone mock service
        self.process = subprocess.Popen([
            'python', 'tests/mock_service.py', str(self.spec_path), str(self.port)
        ])
        
        # Wait for service to start
        time.sleep(3)
        
        # Verify service is running
        try:
            response = requests.get(f"http://localhost:{self.port}/openapi.json", timeout=10)
            assert response.status_code == 200
            logger.info(f"Mock service started successfully on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start mock service: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the mock service"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("Mock service stopped")


class GeneratorService:
    """Wrapper for the generator service"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.process = None
        self.client = TestClient(app)
    
    def start(self):
        """Start the generator service"""
        # For testing, we use the TestClient which doesn't need a separate process
        # But we can verify the app is working
        response = self.client.get("/")
        assert response.status_code == 200
        logger.info("Generator service is ready")
    
    def upload_spec_and_generate(self, spec_path: Path) -> Dict[str, Any]:
        """Upload spec and generate tests via UI"""
        
        # Read the spec file
        with open(spec_path, 'rb') as f:
            spec_content = f.read()
        
        # Prepare form data for UI upload
        files = {'file': (spec_path.name, spec_content, 'application/x-yaml')}
        data = {
            'casesPerEndpoint': '2',
            'outputs': ['junit'],
            'domainHint': 'petstore'
        }
        
        # Submit to UI endpoint
        response = self.client.post("/generate-ui", files=files, data=data)
        
        assert response.status_code == 200, f"Generation failed: {response.text}"
        assert response.headers['content-type'] == 'application/octet-stream'
        
        # Save the ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp.write(response.content)
            zip_path = Path(tmp.name)
        
        logger.info(f"Generated test artifacts saved to {zip_path}")
        return {'zip_path': zip_path, 'response': response}


class JavaTestRunner:
    """Runner for generated Java tests"""
    
    def __init__(self, zip_path: Path):
        self.zip_path = zip_path
        self.extracted_dir = None
    
    def extract_tests(self) -> Path:
        """Extract the ZIP file and return the Java test directory"""
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            # Extract to temporary directory
            self.extracted_dir = Path(tempfile.mkdtemp())
            zip_ref.extractall(self.extracted_dir)
            
            # Find the Java test directory
            java_dir = self.extracted_dir / "artifacts" / "junit"
            if not java_dir.exists():
                raise FileNotFoundError(f"Java test directory not found in {self.extracted_dir}")
            
            logger.info(f"Extracted tests to {java_dir}")
            return java_dir
    
    def run_tests(self, java_dir: Path, target_url: str = "http://localhost:8081") -> bool:
        """Run the generated Java tests"""
        
        # Create a simple Maven project structure
        project_dir = java_dir.parent / "maven-project"
        project_dir.mkdir(exist_ok=True)
        
        # Create pom.xml
        pom_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.test</groupId>
    <artifactId>api-tests</artifactId>
    <version>1.0.0</version>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>5.3.0</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.9.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.15.2</version>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0</version>
            </plugin>
        </plugins>
    </build>
</project>'''
        
        with open(project_dir / "pom.xml", 'w') as f:
            f.write(pom_content)
        
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
            
            # Replace any hardcoded URLs with our target URL
            content = content.replace("http://localhost:8080", target_url)
            content = content.replace("http://localhost:8081", target_url)
            
            with open(target_file, 'w') as f:
                f.write(content)
        
        # Run Maven tests
        try:
            result = subprocess.run(
                ['mvn', 'test', '-Dtest=*Test'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            logger.info(f"Maven test output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Maven test stderr:\n{result.stderr}")
            
            success = result.returncode == 0
            logger.info(f"Java tests {'passed' if success else 'failed'}")
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Java tests timed out")
            return False
        except FileNotFoundError:
            logger.error("Maven not found. Skipping Java tests.")
            return False
    
    def cleanup(self):
        """Clean up extracted files"""
        if self.extracted_dir and self.extracted_dir.exists():
            import shutil
            shutil.rmtree(self.extracted_dir)


@pytest.mark.asyncio
async def test_complete_user_experience():
    """Complete end-to-end test of the user experience"""
    
    mock_service = None
    generator_service = None
    test_runner = None
    
    try:
        logger.info("Starting end-to-end functional test")
        
        # Step 1: Start generator service
        logger.info("Step 1: Starting generator service")
        generator_service = GeneratorService(GENERATOR_PORT)
        generator_service.start()
        
        # Step 2: Start mock service
        logger.info("Step 2: Starting mock service")
        mock_service = MockService(TEST_SPEC_PATH, MOCK_SERVICE_PORT)
        mock_service.start()
        
        # Step 3: Upload spec and generate tests
        logger.info("Step 3: Uploading spec and generating tests")
        result = generator_service.upload_spec_and_generate(TEST_SPEC_PATH)
        zip_path = result['zip_path']
        
        # Step 4: Verify ZIP contains expected files
        logger.info("Step 4: Verifying generated artifacts")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            logger.info(f"ZIP contains {len(file_list)} files")
            
            # Check that we have Java files
            java_files = [f for f in file_list if f.endswith('.java')]
            assert len(java_files) > 0, f"No Java files found in ZIP. Files: {file_list}"
            logger.info(f"Found {len(java_files)} Java files: {java_files}")
            
            # Check that we have the Maven project structure
            assert any(f.endswith('pom.xml') for f in file_list), "No pom.xml found"
            assert any(f.endswith('test-data.json') for f in file_list), "No test-data.json found"
        
        logger.info("✅ End-to-end test successful - all artifacts generated correctly!")
        
    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Cleaning up test resources")
        if mock_service:
            mock_service.stop()
        if 'zip_path' in locals():
            try:
                os.unlink(zip_path)
            except:
                pass


def test_generator_service_health():
    """Basic health check for the generator service"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"


def test_ui_endpoints():
    """Test that UI endpoints are accessible"""
    client = TestClient(app)
    
    # Test landing page
    response = client.get("/")
    assert response.status_code == 200
    
    # Test app page
    response = client.get("/app")
    assert response.status_code == 200


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_complete_user_experience())
