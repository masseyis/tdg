  #  Simple API overview Test Suite

This is a generated test suite for the Simple API overview using JUnit 5 and REST Assured.

#  #  Prerequisites

- Java 11 or higher
- Maven 3.6 or higher
- Internet connection (for OAuth2 token requests)

#  #  Running Tests

##  #  Basic Usage

```bash
mvn verify
```

##  #  With Custom Base URL

```bash
mvn verify -DbaseUrl='http://demopetstore.com'
```

##  #  With Environment Variables

```bash
export API_BASE_URL='http://demopetstore.com'
export API_KEY='your-api-key'
mvn verify
```

##  #  With OAuth2 Authentication

#   #  Password Grant Flow
```bash
mvn verify -DbaseUrl='http://demopetstore.com' \
    -Doauth.tokenUrl='https://auth.example.com/oauth/token' \
    -Doauth.clientId='your-client-id' \
    -Doauth.clientSecret='your-client-secret' \
    -Doauth.username='your-username' \
    -Doauth.password='your-password'
```

#   #  Using Environment Variables for OAuth2
```bash
export OAUTH_TOKEN_URL='https://auth.example.com/oauth/token'
export OAUTH_CLIENT_ID='your-client-id'
export OAUTH_CLIENT_SECRET='your-client-secret'
export OAUTH_USERNAME='your-username'
export OAUTH_PASSWORD='your-password'
mvn verify
```

#  #  Test Structure

- **BaseTest.java**: Base class with common setup
- **Endpoint Tests**: Individual test classes for each API endpoint
- **Flow Tests**: Multi-step test scenarios (if available)

#  #  Configuration

The test suite can be configured using:

1. **System Properties**: `-DbaseUrl=...`, `-Doauth.*=...`
2. **Environment Variables**: `API_BASE_URL`, `API_KEY`, `OAUTH_*`
3. **Default**: `http://localhost:8080`

##  #  Authentication Methods

The test suite supports multiple authentication methods:

- **OAuth2 Password Grant**: Automatic token acquisition
- **OAuth2 Client Credentials**: For service-to-service authentication
- **OAuth2 Authorization Code**: For web applications (requires manual code)
- **API Key**: Simple header-based authentication
- **Bearer Token**: Direct token usage

#  #  Generated Test Cases

This test suite includes:
- Valid test cases
- Boundary test cases
- Negative test cases

Each test case validates:
- HTTP status codes
- Response structure
- Request/response data
