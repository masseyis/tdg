"""
Node.js test renderer using shared JSON test data
"""

import json
from typing import Any, Dict, List


def render(cases: List[Any], api: Any, flows: List[Any] = None) -> Dict[str, str]:
    """
    Render Node.js test files using shared JSON test data
    
    Returns:
        Dictionary of filename -> content
    """
    files = {}
    
    # Generate shared test data JSON file
    files["test-data.json"] = _generate_test_data_json(cases)
    
    # Generate main Node.js test runner
    files["test_api.js"] = _generate_test_runner(cases, api)
    
    # Generate package.json
    files["package.json"] = _generate_package_json()
    
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
    """Generate Node.js test runner"""
    return f'''#!/usr/bin/env node
/**
 * Node.js API Test Runner
 * Generated from: {api.title or "API Specification"}
 * 
 * This test suite uses shared JSON test data for cross-platform compatibility.
 */

const fs = require('fs');
const axios = require('axios');
const path = require('path');

class APITestRunner {{
    /**
     * Test runner for API endpoints using shared JSON test data
     * @param {{string}} baseUrl - Base URL for the API
     * @param {{string}} apiKey - Optional API key for authentication
     * @param {{Object}} oauthConfig - Optional OAuth configuration
     */
    constructor(baseUrl, apiKey = null, oauthConfig = null) {{
        this.baseUrl = baseUrl.replace(/\\/$/, '');
        this.apiKey = apiKey;
        this.oauthConfig = oauthConfig;
        this.testData = null;
        this.accessToken = null;
        this.defaultHeaders = {{
            'Content-Type': 'application/json'
        }};
        
        // Setup authentication
        this.setupAuth();
    }}
    
    setupAuth() {{
        if (this.apiKey) {{
            this.defaultHeaders['api_key'] = this.apiKey;
        }}
        
        if (this.oauthConfig) {{
            this.setupOAuth();
        }}
    }}
    
    async setupOAuth() {{
        if (!this.oauthConfig) return;
        
        try {{
            // Try password grant first
            if (this.oauthConfig.username && this.oauthConfig.password && this.oauthConfig.client_id) {{
                this.accessToken = await this.getOAuthPasswordToken();
            }}
            // Try client credentials
            else if (this.oauthConfig.client_id && this.oauthConfig.client_secret) {{
                this.accessToken = await this.getOAuthClientCredentialsToken();
            }}
            
            if (this.accessToken) {{
                this.defaultHeaders['Authorization'] = `Bearer ${{this.accessToken}}`;
            }}
        }} catch (error) {{
            console.warn(`Warning: OAuth setup failed: ${{error.message}}`);
        }}
    }}
    
    async getOAuthPasswordToken() {{
        const tokenUrl = `${{this.baseUrl}}/oauth/token`;
        const data = {{
            grant_type: 'password',
            username: this.oauthConfig.username,
            password: this.oauthConfig.password,
            client_id: this.oauthConfig.client_id
        }};
        
        try {{
            const response = await axios.post(tokenUrl, data);
            return response.data.access_token;
        }} catch (error) {{
            console.warn(`OAuth password grant failed: ${{error.message}}`);
            return null;
        }}
    }}
    
    async getOAuthClientCredentialsToken() {{
        const tokenUrl = `${{this.baseUrl}}/oauth/token`;
        const data = {{
            grant_type: 'client_credentials',
            client_id: this.oauthConfig.client_id,
            client_secret: this.oauthConfig.client_secret
        }};
        
        try {{
            const response = await axios.post(tokenUrl, data);
            return response.data.access_token;
        }} catch (error) {{
            console.warn(`OAuth client credentials failed: ${{error.message}}`);
            return null;
        }}
    }}
    
    loadTestData(jsonFile = 'test-data.json') {{
        try {{
            const data = fs.readFileSync(jsonFile, 'utf8');
            this.testData = JSON.parse(data);
            console.log(`✅ Loaded ${{this.testData.metadata.total_cases}} test cases`);
        }} catch (error) {{
            console.error(`❌ Error loading test data: ${{error.message}}`);
            process.exit(1);
        }}
    }}
    
    async runTestCase(testCase) {{
        const method = testCase.method.toLowerCase();
        let url = `${{this.baseUrl}}${{testCase.path}}`;
        
        // Apply path parameters
        const pathParams = testCase.path_params || {{}};
        for (const [key, value] of Object.entries(pathParams)) {{
            url = url.replace(`${{{{key}}}}`, value);
        }}
        
        // Prepare request configuration
        const config = {{
            method: method,
            url: url,
            headers: {{
                ...this.defaultHeaders,
                ...testCase.headers
            }},
            params: testCase.query_params || {{}},
            validateStatus: () => true // Don't throw on HTTP error status
        }};
        
        // Add body for POST/PUT requests
        if (testCase.body) {{
            config.data = testCase.body;
        }}
        
        try {{
            const response = await axios(config);
            
            if (response.status === testCase.expected_status) {{
                console.log(`✅ ${{testCase.name}} - PASSED`);
                return true;
            }} else {{
                console.log(`❌ ${{testCase.name}} - FAILED: Expected ${{testCase.expected_status}}, got ${{response.status}}`);
                if (response.data) {{
                    console.log(`   Response: ${{JSON.stringify(response.data).substring(0, 200)}}...`);
                }}
                return false;
            }}
        }} catch (error) {{
            console.log(`❌ ${{testCase.name}} - ERROR: ${{error.message}}`);
            return false;
        }}
    }}
    
    async runAllTests() {{
        if (!this.testData) {{
            console.error('❌ No test data loaded. Call loadTestData() first.');
            return {{ passed: 0, failed: 0 }};
        }}
        
        console.log(`🧪 Running ${{this.testData.metadata.total_cases}} test cases...`);
        console.log(`📊 Generated by: ${{this.testData.metadata.generator}}`);
        console.log(`🔗 Target URL: ${{this.baseUrl}}`);
        console.log('-'.repeat(50));
        
        let passed = 0;
        let failed = 0;
        
        for (const testCase of this.testData.test_cases) {{
            if (await this.runTestCase(testCase)) {{
                passed++;
            }} else {{
                failed++;
            }}
        }}
        
        console.log('-'.repeat(50));
        console.log(`📈 Results: ${{passed}} passed, ${{failed}} failed`);
        
        return {{ passed, failed }};
    }}
}}

async function main() {{
    const args = process.argv.slice(2);
    
    if (args.length < 1) {{
        console.log('Usage: node test_api.js <base_url> [api_key] [oauth_config_file]');
        console.log('');
        console.log('Examples:');
        console.log('  node test_api.js http://localhost:8080');
        console.log('  node test_api.js http://localhost:8080 your-api-key');
        console.log('  node test_api.js http://localhost:8080 your-api-key oauth.json');
        process.exit(1);
    }}
    
    const baseUrl = args[0];
    const apiKey = args[1] || null;
    let oauthConfig = null;
    
    // Load OAuth config if provided
    if (args.length > 2) {{
        try {{
            const oauthData = fs.readFileSync(args[2], 'utf8');
            oauthConfig = JSON.parse(oauthData);
        }} catch (error) {{
            console.warn(`Warning: Could not load OAuth config: ${{error.message}}`);
        }}
    }}
    
    // Create test runner
    const runner = new APITestRunner(baseUrl, apiKey, oauthConfig);
    
    // Load test data
    runner.loadTestData();
    
    // Run tests
    const results = await runner.runAllTests();
    
    // Exit with appropriate code
    if (results.failed > 0) {{
        process.exit(1);
    }}
}}

// Run if this file is executed directly
if (require.main === module) {{
    main().catch(error => {{
        console.error('Unexpected error:', error);
        process.exit(1);
    }});
}}
'''


def _generate_package_json() -> str:
    """Generate package.json for Node.js dependencies"""
    return """{
  "name": "api-tests",
  "version": "1.0.0",
  "description": "Generated API test suite using shared JSON test data",
  "main": "test_api.js",
  "scripts": {
    "test": "node test_api.js",
    "test:help": "node test_api.js"
  },
  "dependencies": {
    "axios": "^1.6.0"
  },
  "engines": {
    "node": ">=14.0.0"
  },
  "keywords": [
    "api",
    "testing",
    "json",
    "axios"
  ],
  "author": "Test Data Generator MVP",
  "license": "MIT"
}
"""


def _generate_readme(api: Any) -> str:
    """Generate README for Node.js tests"""
    return f"""# Node.js API Tests

Generated Node.js test suite for {api.title or "API"} using shared JSON test data.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run tests:
```bash
# Basic usage
node test_api.js http://localhost:8080

# With API key
node test_api.js http://localhost:8080 your-api-key

# With OAuth (create oauth.json first)
node test_api.js http://localhost:8080 your-api-key oauth.json
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
- ✅ Async/await support
- ✅ Axios HTTP client

## Requirements

- Node.js 14.0.0 or higher
- npm or yarn package manager
"""
