"""
Python test renderer using shared JSON test data
"""

import json
from typing import Any, Dict, List


def render(cases: List[Any], api: Any, flows: List[Any] = None) -> Dict[str, str]:
    """
    Render Python test files using shared JSON test data
    
    Returns:
        Dictionary of filename -> content
    """
    files = {}
    
    # Generate shared test data JSON file
    files["test-data.json"] = _generate_test_data_json(cases)
    
    # Generate main Python test runner
    files["test_api.py"] = _generate_test_runner(cases, api)
    
    # Generate requirements.txt
    files["requirements.txt"] = _generate_requirements()
    
    # Generate README
    files["README.md"] = _generate_readme(api)
    
    return files


def _generate_test_data_json(cases: List[Any]) -> str:
    """Generate shared test data as JSON file"""
    test_data = {
        "metadata": {
            "generated_at": "2024-01-01T00:00:00Z",
            "generator": "Test Data Generator MVP",
            "version": "1.0.0",
            "total_cases": len(cases)
        },
        "test_cases": []
    }
    
    for case in cases:
        test_case = {
            "id": case.name,
            "name": case.name,
            "description": case.description,
            "method": case.method,
            "path": case.path,
            "headers": case.headers or {},
            "query_params": case.query_params or {},
            "path_params": case.path_params or {},
            "body": case.body,
            "expected_status": case.expected_status,
            "expected_response": case.expected_response,
            "test_type": case.test_type
        }
        test_data["test_cases"].append(test_case)
    
    return json.dumps(test_data, indent=2)


def _generate_test_runner(cases: List[Any], api: Any) -> str:
    """Generate Python test runner"""
    return f'''#!/usr/bin/env python3
"""
Python API Test Runner
Generated from: {api.title or "API Specification"}

This test suite uses shared JSON test data for cross-platform compatibility.
"""

import json
import requests
import sys
import os
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class APITestRunner:
    """Test runner for API endpoints using shared JSON test data"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 oauth_config: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.oauth_config = oauth_config
        self.session = requests.Session()
        self.test_data = None
        self.access_token = None
        
        # Setup authentication
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication headers"""
        if self.api_key:
            self.session.headers.update({{'api_key': self.api_key}})
        
        if self.oauth_config:
            self._setup_oauth()
    
    def _setup_oauth(self):
        """Setup OAuth2 authentication"""
        if not self.oauth_config:
            return
            
        try:
            # Try password grant first
            if all(k in self.oauth_config for k in ['username', 'password', 'client_id']):
                self.access_token = self._get_oauth_password_token()
            # Try client credentials
            elif 'client_id' in self.oauth_config and 'client_secret' in self.oauth_config:
                self.access_token = self._get_oauth_client_credentials_token()
            
            if self.access_token:
                self.session.headers.update({{'Authorization': f'Bearer {{self.access_token}}'}})
        except Exception as e:
            print(f"Warning: OAuth setup failed: {{e}}")
    
    def _get_oauth_password_token(self) -> Optional[str]:
        """Get OAuth2 token using password grant"""
        token_url = urljoin(self.base_url, '/oauth/token')
        data = {{
            'grant_type': 'password',
            'username': self.oauth_config['username'],
            'password': self.oauth_config['password'],
            'client_id': self.oauth_config['client_id']
        }}
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        return None
    
    def _get_oauth_client_credentials_token(self) -> Optional[str]:
        """Get OAuth2 token using client credentials"""
        token_url = urljoin(self.base_url, '/oauth/token')
        data = {{
            'grant_type': 'client_credentials',
            'client_id': self.oauth_config['client_id'],
            'client_secret': self.oauth_config['client_secret']
        }}
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        return None
    
    def load_test_data(self, json_file: str = "test-data.json"):
        """Load test data from JSON file"""
        try:
            with open(json_file, 'r') as f:
                self.test_data = json.load(f)
            print(f"✅ Loaded {{self.test_data['metadata']['total_cases']}} test cases")
        except Exception as e:
            print(f"❌ Error loading test data: {{e}}")
            sys.exit(1)
    
    def run_test_case(self, test_case: Dict[str, Any]) -> bool:
        """Execute a single test case"""
        method = test_case['method'].upper()
        path = test_case['path']
        
        # Build full URL
        url = urljoin(self.base_url, path)
        
        # Apply path parameters
        path_params = test_case.get('path_params', {{}})
        for key, value in path_params.items():
            url = url.replace('{{' + key + '}}', str(value))
        
        # Prepare request parameters
        headers = {{**test_case.get('headers', {{}})}}
        params = test_case.get('query_params', {{}})
        body = test_case.get('body')
        expected_status = test_case['expected_status']
        
        try:
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body if body else None
            )
            
            # Check status code
            if response.status_code == expected_status:
                print(f"✅ {{test_case['name']}} - PASSED")
                return True
            else:
                print(f"❌ {{test_case['name']}} - FAILED: Expected {{expected_status}}, got {{response.status_code}}")
                if response.text:
                    print(f"   Response: {{response.text[:200]}}...")
                return False
                
        except Exception as e:
            print(f"❌ {{test_case['name']}} - ERROR: {{e}}")
            return False
    
    def run_all_tests(self) -> Dict[str, int]:
        """Run all test cases and return results"""
        if not self.test_data:
            print("❌ No test data loaded. Call load_test_data() first.")
            return {{'passed': 0, 'failed': 0}}
        
        print(f"🧪 Running {{self.test_data['metadata']['total_cases']}} test cases...")
        print(f"📊 Generated by: {{self.test_data['metadata']['generator']}}")
        print(f"🔗 Target URL: {{self.base_url}}")
        print("-" * 50)
        
        passed = 0
        failed = 0
        
        for test_case in self.test_data['test_cases']:
            if self.run_test_case(test_case):
                passed += 1
            else:
                failed += 1
        
        print("-" * 50)
        print(f"📈 Results: {{passed}} passed, {{failed}} failed")
        
        return {{'passed': passed, 'failed': failed}}


def main():
    """Main function to run tests"""
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <base_url> [api_key] [oauth_config_file]")
        print("")
        print("Examples:")
        print("  python test_api.py http://localhost:8080")
        print("  python test_api.py http://localhost:8080 your-api-key")
        print("  python test_api.py http://localhost:8080 your-api-key oauth.json")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    oauth_config = None
    
    # Load OAuth config if provided
    if len(sys.argv) > 3:
        try:
            with open(sys.argv[3], 'r') as f:
                oauth_config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load OAuth config: {{e}}")
    
    # Create test runner
    runner = APITestRunner(base_url, api_key, oauth_config)
    
    # Load test data
    runner.load_test_data()
    
    # Run tests
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


def _generate_requirements() -> str:
    """Generate requirements.txt for Python dependencies"""
    return """requests>=2.25.0
urllib3>=1.26.0
"""


def _generate_readme(api: Any) -> str:
    """Generate README for Python tests"""
    return f"""# Python API Tests

Generated Python test suite for {api.title or "API"} using shared JSON test data.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
# Basic usage
python test_api.py http://localhost:8080

# With API key
python test_api.py http://localhost:8080 your-api-key

# With OAuth (create oauth.json first)
python test_api.py http://localhost:8080 your-api-key oauth.json
```

## OAuth Configuration

Create `oauth.json` for OAuth2 authentication:
```json
{{
    "username": "user",
    "password": "password",
    "client_id": "client_id",
    "client_secret": "client_secret"
}}
```

## Test Data

Tests use `test-data.json` which is shared across all frameworks (Java, Python, Node.js, Postman).

## Features

- ✅ Shared JSON test data
- ✅ API Key authentication
- ✅ OAuth2 support (password grant, client credentials)
- ✅ Path parameter substitution
- ✅ Query parameter handling
- ✅ Request body support
- ✅ Status code validation
- ✅ Detailed error reporting
"""
