# Node.js API Tests

Generated Node.js test suite for OpenAPI Petstore using shared JSON test data.

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
{
    "username": "user",
    "password": "password",
    "client_id": "client_id",
    "client_secret": "client_secret"
}
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
