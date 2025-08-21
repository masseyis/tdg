# Test Data Generator (TDG) MVP

A powerful OpenAPI test case generator that creates comprehensive test suites for REST APIs with support for OAuth2 authentication and multiple output formats.

## 🚀 Features

- **OpenAPI Specification Processing**: Loads and normalizes OpenAPI/Swagger specifications
- **AI-Powered Test Generation**: Uses AI to generate realistic test cases
- **Multiple Output Formats**: 
  - JUnit/REST Assured (Java)
  - Postman Collections
  - JSON
  - CSV
  - SQL
- **OAuth2 Support**: Full OAuth2 authentication framework with password grant, client credentials, and authorization code flows
- **API Key Authentication**: Support for API key authentication
- **Complete Maven Projects**: Generates ready-to-run Maven projects with all dependencies
- **Query & Path Parameter Handling**: Properly handles all parameter types
- **Test Data Management**: Creates and cleans up test data automatically

## 📋 Prerequisites

- Python 3.8+
- Java 11+ (for running generated tests)
- Maven (for running generated tests)
- Internet connection (for OAuth2 token requests)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd tdg-mvp
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Install development dependencies** (optional):
   ```bash
   make install-dev
   ```

## 🚀 Quick Start

### 1. Start the Development Server

```bash
make dev
```

The server will start at `http://localhost:8000`

### 2. Generate Test Cases

#### From OpenAPI Specification File

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "spec_url": "http://localhost:8081/openapi.json",
    "cases_per_endpoint": 3,
    "outputs": ["junit"],
    "domain_hint": "petstore"
  }'
```

#### From Local File

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "spec_file": "examples/petstore.json",
    "cases_per_endpoint": 3,
    "outputs": ["junit", "postman", "json"],
    "domain_hint": "petstore"
  }'
```

### 3. Run Generated Tests

#### API Key Only (Fully Passing)

```bash
mvn test -Dtest=ComprehensiveTestFlow -DbaseUrl=http://localhost:8081/v3 -DapiKey=special-key
```

#### OAuth2 Infrastructure Test

```bash
mvn test -Dtest=OAuth2TestFlow -DbaseUrl=http://localhost:8081/v3 -DapiKey=special-key -Doauth.tokenUrl=http://localhost:8081/oauth/token -Doauth.clientId=petstore -Doauth.clientSecret=petstore -Doauth.username=user -Doauth.password=user
```

#### Combined Test Suite

```bash
mvn test -Dtest=ComprehensiveTestFlow,OAuth2TestFlow -DbaseUrl=http://localhost:8081/v3 -DapiKey=special-key -Doauth.tokenUrl=http://localhost:8081/oauth/token -Doauth.clientId=petstore -Doauth.clientSecret=petstore -Doauth.username=user -Doauth.password=user
```

## 🔧 Configuration

### Environment Variables

- `API_KEY`: API key for authentication
- `OAUTH_TOKEN_URL`: OAuth2 token endpoint URL
- `OAUTH_CLIENT_ID`: OAuth2 client ID
- `OAUTH_CLIENT_SECRET`: OAuth2 client secret
- `OAUTH_USERNAME`: OAuth2 username
- `OAUTH_PASSWORD`: OAuth2 password

### System Properties (for Maven tests)

- `-DbaseUrl`: Base URL for the API
- `-DapiKey`: API key for authentication
- `-Doauth.tokenUrl`: OAuth2 token endpoint URL
- `-Doauth.clientId`: OAuth2 client ID
- `-Doauth.clientSecret`: OAuth2 client secret
- `-Doauth.username`: OAuth2 username
- `-Doauth.password`: OAuth2 password

## 📁 Project Structure

```
tdg-mvp/
├── app/
│   ├── ai/                    # AI providers (OpenAI, Anthropic, etc.)
│   ├── generation/            # Test case generation logic
│   │   └── renderers/         # Output format renderers
│   ├── utils/                 # Utility functions
│   ├── main.py               # FastAPI application
│   └── schemas.py            # Pydantic schemas
├── examples/                 # Example OpenAPI specifications
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── Makefile                 # Build and development commands
└── README.md               # This file
```

## 🔐 Authentication Support

### API Key Authentication

The generator supports API key authentication for endpoints that don't require OAuth2:

```java
// Generated test will include API key header
.header("api_key", "special-key")
```

### OAuth2 Authentication

Full OAuth2 support with multiple flows:

#### Password Grant Flow

```java
// Automatically handles OAuth2 password grant
String token = getOAuth2Token(tokenUrl, clientId, clientSecret, username, password);
```

#### Client Credentials Flow

```java
// For machine-to-machine authentication
String token = getClientCredentialsToken(tokenUrl, clientId, clientSecret);
```

#### Authorization Code Flow

```java
// For web applications
String token = getAuthorizationCodeToken(tokenUrl, clientId, clientSecret, code, redirectUri);
```

## 🧪 Test Output Formats

### JUnit/REST Assured (Java)

Generates complete Maven projects with:
- `pom.xml` with all dependencies
- `BaseTest.java` with authentication logic
- Individual test classes for each endpoint
- `ComprehensiveTestFlow.java` for full test cycles
- `OAuth2TestFlow.java` for OAuth2 testing

### Postman Collections

Exports test cases as Postman collections with:
- Environment variables
- Pre-request scripts
- Test scripts
- Authentication headers

### JSON

Raw test case data in JSON format for custom processing.

### CSV

Test cases in CSV format for spreadsheet analysis.

### SQL

SQL scripts for database setup and cleanup.

## 🚀 Example Usage

### 1. Start a Test API Server

```bash
# Start Petstore API (example)
docker pull openapitools/openapi-petstore
docker run -d -e OPENAPI_BASE_PATH=/v3 -p 8081:8081 openapitools/openapi-petstore
```

### 2. Generate Tests

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "spec_url": "http://localhost:8081/openapi.json",
    "cases_per_endpoint": 2,
    "outputs": ["junit"],
    "domain_hint": "petstore"
  }'
```

### 3. Extract and Run Tests

```bash
# Extract the generated Maven project
unzip generated_tests.zip
cd generated_tests

# Run the comprehensive test suite
mvn test -Dtest=ComprehensiveTestFlow,OAuth2TestFlow \
  -DbaseUrl=http://localhost:8081/v3 \
  -DapiKey=special-key \
  -Doauth.tokenUrl=http://localhost:8081/oauth/token \
  -Doauth.clientId=petstore \
  -Doauth.clientSecret=petstore \
  -Doauth.username=user \
  -Doauth.password=user
```

## 🧪 Testing

Run the test suite:

```bash
make test
```

## 🛠️ Development

### Running in Development Mode

```bash
make dev
```

### Installing Development Dependencies

```bash
make install-dev
```

### Running Tests

```bash
make test
```

## 📝 API Reference

### POST /generate

Generate test cases from an OpenAPI specification.

**Request Body:**
```json
{
  "spec_url": "string",           // URL to OpenAPI specification
  "spec_file": "string",          // Local file path (alternative to spec_url)
  "cases_per_endpoint": 3,        // Number of test cases per endpoint
  "outputs": ["junit", "postman"], // Output formats
  "domain_hint": "string"         // Domain context for AI generation
}
```

**Response:**
- `junit`: ZIP file containing Maven project
- `postman`: JSON file containing Postman collection
- `json`: JSON file containing test cases
- `csv`: CSV file containing test cases
- `sql`: SQL file containing database scripts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the example files in `/examples`

## 🎯 Roadmap

- [ ] Support for GraphQL APIs
- [ ] gRPC test generation
- [ ] Performance test generation
- [ ] Visual test report generation
- [ ] Integration with CI/CD pipelines
- [ ] Custom test templates
- [ ] Multi-language support (Python, JavaScript, Go)
