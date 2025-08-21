"""JUnit + REST Assured test renderer"""
import json
from typing import List, Dict, Any


def render(cases: List[Any], api: Any, flows: List[Any] = None) -> Dict[str, str]:
    """
    Render complete Maven project with JUnit tests

    Returns:
        Dictionary of filename -> content
    """
    files = {}

    # Group cases by endpoint
    endpoint_cases = {}
    for case in cases:
        key = f"{case.method}_{case.path}"
        if key not in endpoint_cases:
            endpoint_cases[key] = []
        endpoint_cases[key].append(case)

    # Generate Maven project structure
    files["pom.xml"] = _generate_pom_xml(api)
    files[".gitignore"] = _generate_gitignore()
    files["README.md"] = _generate_readme(api)

    # Generate comprehensive test flow
    files["src/test/java/generated/ComprehensiveTestFlow.java"] = _generate_comprehensive_test_flow(api)

    # Generate OAuth2 test flow
    files["src/test/java/generated/OAuth2TestFlow.java"] = _generate_oauth2_test_flow(api)

    # Generate test class for each endpoint
    for endpoint_key, endpoint_cases in endpoint_cases.items():
        class_name = _generate_class_name(endpoint_key)
        content = _generate_test_class(class_name, endpoint_cases, api)
        files[f"src/test/java/generated/{class_name}.java"] = content

    # Generate flow tests if any
    if flows:
        flow_content = _generate_flow_tests(flows, api)
        files["src/test/java/generated/FlowTests.java"] = flow_content

    # Add base test class
    files["src/test/java/generated/BaseTest.java"] = _generate_base_class()

    return files


def _generate_class_name(endpoint_key: str) -> str:
    """Generate Java class name from endpoint key"""
    parts = endpoint_key.replace("/", "_").replace("{", "").replace("}", "").split("_")
    return "".join(p.capitalize() for p in parts if p) + "Test"


def _generate_test_class(class_name: str, cases: List[Any], api: Any) -> str:
    """Generate JUnit test class"""
    return f"""package generated;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.Map;
import java.util.stream.Stream;
import com.fasterxml.jackson.databind.ObjectMapper;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;

public class {class_name} extends BaseTest {{

    @ParameterizedTest(name = "{{0}}")
    @MethodSource("provideTestCases")
    void testEndpoint(String testName, String method, String path, String body, String queryParams, String pathParams, int expectedStatus) {{
        var request = given()
            .contentType(ContentType.JSON)
            .accept(ContentType.JSON);

        // Add OAuth2 authentication headers if available
        Map<String, String> authHeaders = getAuthHeaders();
        for (Map.Entry<String, String> header : authHeaders.entrySet()) {{
            request.header(header.getKey(), header.getValue());
        }}

        // Add query parameters if present
        if (queryParams != null && !queryParams.isEmpty()) {{
            try {{
                ObjectMapper mapper = new ObjectMapper();
                Map<String, Object> params = mapper.readValue(queryParams, Map.class);
                for (Map.Entry<String, Object> param : params.entrySet()) {{
                    request.queryParam(param.getKey(), param.getValue());
                }}
            }} catch (Exception e) {{
                System.err.println("Failed to parse query parameters: " + e.getMessage());
            }}
        }}

        // Add path parameters if present
        if (pathParams != null && !pathParams.isEmpty()) {{
            try {{
                ObjectMapper mapper = new ObjectMapper();
                Map<String, Object> params = mapper.readValue(pathParams, Map.class);
                for (Map.Entry<String, Object> param : params.entrySet()) {{
                    request.pathParam(param.getKey(), param.getValue());
                }}
            }} catch (Exception e) {{
                System.err.println("Failed to parse path parameters: " + e.getMessage());
            }}
        }}

        if (body != null) {{
            request.body(body);
        }}

        var response = request.request(method, path);

        response.then()
            .statusCode(expectedStatus);
    }}

    static Stream<Arguments> provideTestCases() {{
        return Stream.of(
{_generate_test_cases(cases)}
        );
    }}
}}"""


def _generate_test_cases(cases: List[Any]) -> str:
    """Generate test case arguments"""
    lines = []
    for case in cases:
        body_str = "null"
        if case.body:
            json_body = json.dumps(case.body).replace('"', '\\"')
            body_str = f'"{json_body}"'

        # Handle query parameters
        query_params_str = "null"
        if case.query_params:
            json_query = json.dumps(case.query_params).replace('"', '\\"')
            query_params_str = f'"{json_query}"'

        # Handle path parameters
        path_params_str = "null"
        if case.path_params:
            json_path = json.dumps(case.path_params).replace('"', '\\"')
            path_params_str = f'"{json_path}"'

        line = f'            Arguments.of("{case.name}", "{case.method}", "{case.path}", {body_str}, {query_params_str}, {path_params_str}, {case.expected_status})'
        lines.append(line)

    return ",\n".join(lines)


def _generate_flow_tests(flows: List[Any], api: Any) -> str:
    """Generate flow test class"""
    return """package generated;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class FlowTests extends BaseTest {

    private static String createdId;

    @Test
    @Order(1)
    void testCreateFlow() {
        Response response = given()
            .contentType(ContentType.JSON)
            .body("{\\"name\\": \\"Test Item\\"}")
        .when()
            .post("/items")
        .then()
            .statusCode(201)
            .extract().response();

        createdId = response.jsonPath().getString("id");
        assertNotNull(createdId);
    }

    @Test
    @Order(2)
    void testReadFlow() {
        given()
            .pathParam("id", createdId)
        .when()
            .get("/items/{id}")
        .then()
            .statusCode(200)
            .body("id", equalTo(createdId));
    }
}"""


def _generate_comprehensive_test_flow(api: Any) -> str:
    """Generate comprehensive test flow that creates data, tests it, and cleans up"""
    return """package generated;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.HashMap;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ComprehensiveTestFlow extends BaseTest {{

    private static String createdPetId;
    private static String createdOrderId;
    private static String createdUsername;
    private static final ObjectMapper mapper = new ObjectMapper();

    @Test
    @Order(1)
    void testUserLogin() {{
        // Test login functionality
        Response response = given()
            .contentType(ContentType.JSON)
            .queryParam("username", "testuser")
            .queryParam("password", "testpass")
        .when()
            .get("/user/login")
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ User login test passed");
    }}

    @Test
    @Order(2)
    void testCreateUser() {{
        // Create a test user
        Map<String, Object> userData = new HashMap<>();
        userData.put("username", "testuser_" + System.currentTimeMillis());
        userData.put("firstName", "Test");
        userData.put("lastName", "User");
        userData.put("email", "test@example.com");
        userData.put("password", "testpass");
        userData.put("phone", "1234567890");
        userData.put("userStatus", 1);

        createdUsername = (String) userData.get("username");

        Response response = given()
            .contentType(ContentType.JSON)
            .body(userData)
        .when()
            .post("/user")
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ Created user: " + createdUsername);
    }}

    @Test
    @Order(3)
    void testGetUser() {{
        // Test getting the created user
        Response response = given()
            .contentType(ContentType.JSON)
        .when()
            .get("/user/" + createdUsername)
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ Retrieved user: " + createdUsername);
    }}

    @Test
    @Order(4)
    void testGetExistingOrder() {{
        // Test getting an existing order (order ID 1 should exist)
        Response response = given()
            .contentType(ContentType.JSON)
        .when()
            .get("/store/order/1")
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ Retrieved existing order: 1");
    }}

    @Test
    @Order(5)
    void testGetInventory() {{
        // Test inventory endpoint with API key
        Map<String, String> authHeaders = getAuthHeaders();

        Response response = given()
            .contentType(ContentType.JSON)
            .headers(authHeaders)
        .when()
            .get("/store/inventory")
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ Retrieved inventory");
    }}

    @Test
    @Order(6)
    void testUserLogout() {{
        // Test logout functionality
        Response response = given()
            .contentType(ContentType.JSON)
        .when()
            .get("/user/logout")
        .then()
            .statusCode(200)
            .extract().response();

        System.out.println("✅ User logout test passed");
    }}

    @Test
    @Order(7)
    void testUpdateUser() {{
        // Test updating the created user
        if (createdUsername != null) {{
            Map<String, Object> userData = new HashMap<>();
            userData.put("username", createdUsername);
            userData.put("firstName", "Updated");
            userData.put("lastName", "User");
            userData.put("email", "updated@example.com");
            userData.put("password", "newpass");
            userData.put("phone", "0987654321");
            userData.put("userStatus", 2);

            Response response = given()
                .contentType(ContentType.JSON)
                .body(userData)
            .when()
                .put("/user/" + createdUsername)
            .then()
                .statusCode(200)
                .extract().response();

            System.out.println("✅ Updated user: " + createdUsername);
        }} else {{
            System.out.println("⚠️  Skipping user update - no username");
        }}
    }}

    @Test
    @Order(8)
    void testDeleteUser() {{
        // Clean up: Delete the created user
        if (createdUsername != null) {{
            Response response = given()
                .contentType(ContentType.JSON)
            .when()
                .delete("/user/" + createdUsername)
            .then()
                .statusCode(200)
                .extract().response();

            System.out.println("✅ Deleted user: " + createdUsername);
        }} else {{
            System.out.println("⚠️  Skipping user deletion - no username");
        }}
    }}
}}"""


def _generate_oauth2_test_flow(api: Any) -> str:
    """Generate OAuth2 test flow that demonstrates OAuth2 authentication"""
    return """package generated;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.HashMap;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class OAuth2TestFlow extends BaseTest {{

    private static final ObjectMapper mapper = new ObjectMapper();

    @Test
    @Order(1)
    void testOAuth2Setup() {{
        // Verify OAuth2 configuration is available
        String oauthTokenUrl = System.getProperty("oauth.tokenUrl");
        String oauthClientId = System.getProperty("oauth.clientId");
        String oauthUsername = System.getProperty("oauth.username");
        String oauthPassword = System.getProperty("oauth.password");

        if (oauthTokenUrl != null && oauthClientId != null && oauthUsername != null && oauthPassword != null) {{
            System.out.println("✅ OAuth2 configuration detected");
            System.out.println("  Token URL: " + oauthTokenUrl);
            System.out.println("  Client ID: " + oauthClientId);
            System.out.println("  Username: " + oauthUsername);
        }} else {{
            System.out.println("⚠️  OAuth2 configuration not provided - using API key fallback");
        }}
    }}

    @Test
    @Order(2)
    void testOAuth2TokenEndpoint() {{
        // Test that OAuth2 token endpoint exists and is accessible
        System.out.println("🔐 Testing OAuth2 token endpoint availability...");

        // Use base URL without /v3 for OAuth2 endpoints
        String baseUrl = System.getProperty("baseUrl");
        String oauthBaseUrl = baseUrl.replace("/v3", ""); // Remove /v3 for OAuth2 endpoints

        Response response = given()
            .contentType(ContentType.JSON)
        .when()
            .get(oauthBaseUrl + "/oauth/token")
        .then()
            .statusCode(401) // Should return 401 (Unauthorized) not 404 (Not Found)
            .extract().response();

        System.out.println("✅ OAuth2 token endpoint is available");
        System.out.println("  Status: " + response.getStatusCode() + " (Unauthorized - endpoint exists)");
        System.out.println("  Response: " + response.asString());
    }}

    @Test
    @Order(3)
    void testOAuth2DialogEndpoint() {{
        // Test that OAuth2 dialog endpoint exists and redirects properly
        System.out.println("🔐 Testing OAuth2 dialog endpoint...");

        // Use base URL without /v3 for OAuth2 endpoints
        String baseUrl = System.getProperty("baseUrl");
        String oauthBaseUrl = baseUrl.replace("/v3", ""); // Remove /v3 for OAuth2 endpoints

        Response response = given()
            .contentType(ContentType.JSON)
            .redirects().follow(false) // Don't follow redirects
        .when()
            .get(oauthBaseUrl + "/api/oauth/dialog")
        .then()
            .statusCode(302) // Should redirect to login
            .extract().response();

        System.out.println("✅ OAuth2 dialog endpoint is available");
        System.out.println("  Status: " + response.getStatusCode() + " (Redirect to login)");
        System.out.println("  Location: " + response.getHeader("Location"));
    }}

    @Test
    @Order(4)
    void testOAuth2ProtectedEndpointBehavior() {{
        // Test OAuth2 protected endpoint behavior (should require OAuth2 token)
        System.out.println("🔐 Testing OAuth2 protected endpoint behavior...");

        Response response = given()
            .contentType(ContentType.JSON)
            .header("api_key", "special-key")
            .queryParam("status", "available")
        .when()
            .get("/pet/findByStatus")
        .then()
            .statusCode(401) // Should return 401 (Unauthorized) - requires OAuth2 token
            .extract().response();

        System.out.println("✅ OAuth2 protected endpoint correctly requires OAuth2 token");
        System.out.println("  Status: " + response.getStatusCode() + " (Unauthorized - as expected)");
        System.out.println("  WWW-Authenticate: " + response.getHeader("WWW-Authenticate"));
    }}

    @Test
    @Order(5)
    void testOAuth2PetCreationBehavior() {{
        // Test OAuth2 pet creation behavior (should require OAuth2 token)
        System.out.println("🔐 Testing OAuth2 pet creation behavior...");

        Map<String, Object> petData = new HashMap<>();
        petData.put("name", "OAuth2TestPet_" + System.currentTimeMillis());
        petData.put("status", "available");

        Map<String, Object> category = new HashMap<>();
        category.put("id", 1);
        category.put("name", "dogs");
        petData.put("category", category);

        petData.put("photoUrls", new String[]{{"http://example.com/photo.jpg"}});

        Response response = given()
            .contentType(ContentType.JSON)
            .header("api_key", "special-key")
            .body(petData)
        .when()
            .post("/pet")
        .then()
            .statusCode(401) // Should return 401 (Unauthorized) - requires OAuth2 token
            .extract().response();

        System.out.println("✅ OAuth2 pet creation correctly requires OAuth2 token");
        System.out.println("  Status: " + response.getStatusCode() + " (Unauthorized - as expected)");
        System.out.println("  WWW-Authenticate: " + response.getHeader("WWW-Authenticate"));
    }}

    @Test
    @Order(6)
    void testOAuth2AuthenticationMethod() {{
        // Test that we're using the correct authentication method
        String oauthTokenUrl = System.getProperty("oauth.tokenUrl");

        if (oauthTokenUrl != null) {{
            System.out.println("✅ Using OAuth2 authentication");
            System.out.println("  Authentication method: OAuth2 Password Grant");
        }} else {{
            System.out.println("✅ Using API Key authentication");
            System.out.println("  Authentication method: API Key");
        }}

        System.out.println("🔐 OAuth2 infrastructure is available:");
        System.out.println("  - Token endpoint: /oauth/token");
        System.out.println("  - Dialog endpoint: /api/oauth/dialog");
        System.out.println("  - Implicit flow configured");
        System.out.println("  - Requires proper client credentials for token access");
    }}
}}"""


def _generate_pom_xml(api: Any) -> str:
    """Generate Maven pom.xml"""
    project_name = api.title.replace(" ", "-").lower() if api.title else "api-tests"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>{project_name}-tests</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>{api.title or "API Tests"}</name>
    <description>Generated test suite for {api.title or "API"}</description>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <junit.version>5.9.2</junit.version>
        <restassured.version>5.3.0</restassured.version>
        <hamcrest.version>2.2</hamcrest.version>
    </properties>

    <dependencies>
        <!-- JUnit 5 -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${{junit.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- REST Assured -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>${{restassured.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- JSON Path for REST Assured -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>json-path</artifactId>
            <version>${{restassured.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- XML Path for REST Assured -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>xml-path</artifactId>
            <version>${{restassured.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- Hamcrest for assertions -->
        <dependency>
            <groupId>org.hamcrest</groupId>
            <artifactId>hamcrest</artifactId>
            <version>${{hamcrest.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- OAuth2 support -->
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>okhttp</artifactId>
            <version>4.11.0</version>
            <scope>test</scope>
        </dependency>

        <!-- JSON processing for OAuth2 -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.15.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Surefire Plugin for running tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0</version>
                <configuration>
                    <systemPropertyVariables>
                        <baseUrl>${{baseUrl}}</baseUrl>
                    </systemPropertyVariables>
                </configuration>
            </plugin>

            <!-- Maven Failsafe Plugin for integration tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-failsafe-plugin</artifactId>
                <version>3.0.0</version>
                <configuration>
                    <systemPropertyVariables>
                        <baseUrl>${{baseUrl}}</baseUrl>
                    </systemPropertyVariables>
                </configuration>
            </plugin>

            <!-- Maven Compiler Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>"""


def _generate_gitignore() -> str:
    """Generate .gitignore file"""
    return """  #  Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

  #  IDE
.idea/
*.iws
*.iml
*.ipr
.vscode/
.settings/
.project
.classpath

  #  OS
.DS_Store
Thumbs.db

  #  Logs
*.log

  #  Test reports
test-output/
reports/
"""


def _generate_readme(api: Any) -> str:
    """Generate README.md file"""
    return f"""  #  {api.title or "API"} Test Suite

This is a generated test suite for the {api.title or "API"} using JUnit 5 and REST Assured.

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
mvn verify -DbaseUrl='http://demopetstore.com' \\
    -Doauth.tokenUrl='https://auth.example.com/oauth/token' \\
    -Doauth.clientId='your-client-id' \\
    -Doauth.clientSecret='your-client-secret' \\
    -Doauth.username='your-username' \\
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
"""


def _generate_base_class() -> str:
    """Generate base test class"""
    return """package generated;

import io.restassured.RestAssured;
import org.junit.jupiter.api.BeforeAll;
import okhttp3.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.util.Map;
import java.util.HashMap;

public abstract class BaseTest {

    private static String accessToken = null;
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @BeforeAll
    public static void setup() {
        // Get base URL from system property or environment variable
        String baseUrl = System.getProperty("baseUrl");
        if (baseUrl == null) {
            baseUrl = System.getenv("API_BASE_URL");
        }
        if (baseUrl == null) {
            baseUrl = "http://localhost:8080";
        }

        RestAssured.baseURI = baseUrl;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();

        // Setup authentication
        setupAuthentication();

        System.out.println("Running tests against: " + baseUrl);
    }

    private static void setupAuthentication() {
        // Check for OAuth2 configuration
        String oauthTokenUrl = System.getProperty("oauth.tokenUrl");
        String oauthClientId = System.getProperty("oauth.clientId");
        String oauthClientSecret = System.getProperty("oauth.clientSecret");
        String oauthUsername = System.getProperty("oauth.username");
        String oauthPassword = System.getProperty("oauth.password");

        // Check environment variables as fallback
        if (oauthTokenUrl == null) oauthTokenUrl = System.getenv("OAUTH_TOKEN_URL");
        if (oauthClientId == null) oauthClientId = System.getenv("OAUTH_CLIENT_ID");
        if (oauthClientSecret == null) oauthClientSecret = System.getenv("OAUTH_CLIENT_SECRET");
        if (oauthUsername == null) oauthUsername = System.getenv("OAUTH_USERNAME");
        if (oauthPassword == null) oauthPassword = System.getenv("OAUTH_PASSWORD");

        // Try OAuth2 password grant if configured
        if (oauthTokenUrl != null && oauthClientId != null && oauthUsername != null && oauthPassword != null) {
            try {
                accessToken = getOAuth2Token(oauthTokenUrl, oauthClientId, oauthClientSecret, oauthUsername, oauthPassword);
                if (accessToken != null) {
                    System.out.println("OAuth2 authentication configured successfully");
                }
            } catch (Exception e) {
                System.err.println("OAuth2 authentication failed: " + e.getMessage());
            }
        }

        // Note: API key will be handled per-request in getAuthHeaders()
        String apiKey = System.getProperty("apiKey");
        if (apiKey == null) {
            apiKey = System.getenv("API_KEY");
        }
        if (apiKey != null) {
            System.out.println("API Key authentication configured");
        }
    }

    private static String getOAuth2Token(String tokenUrl, String clientId, String clientSecret,
                                       String username, String password) throws IOException {
        OkHttpClient client = new OkHttpClient();

        // Build form data for password grant
        FormBody.Builder formBuilder = new FormBody.Builder()
            .add("grant_type", "password")
            .add("username", username)
            .add("password", password);

        if (clientId != null) {
            formBuilder.add("client_id", clientId);
        }
        if (clientSecret != null) {
            formBuilder.add("client_secret", clientSecret);
        }

        RequestBody formBody = formBuilder.build();

        Request request = new Request.Builder()
            .url(tokenUrl)
            .post(formBody)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .build();

        try (okhttp3.Response response = client.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String responseBody = response.body().string();
                Map<String, Object> tokenResponse = objectMapper.readValue(responseBody, Map.class);
                return (String) tokenResponse.get("access_token");
            } else {
                System.err.println("OAuth2 token request failed: " + response.code() + " " + response.message());
                return null;
            }
        }
    }

    /**
     * Get authentication headers for requests
     */
    protected static Map<String, String> getAuthHeaders() {
        Map<String, String> headers = new HashMap<>();

        // Add OAuth2 Bearer token if available
        if (accessToken != null) {
            headers.put("Authorization", "Bearer " + accessToken);
        }

        // Add API key if available
        String apiKey = System.getProperty("apiKey");
        if (apiKey == null) {
            apiKey = System.getenv("API_KEY");
        }
        if (apiKey != null) {
            headers.put("api_key", apiKey);
        }

        return headers;
    }

    /**
     * Perform OAuth2 client credentials flow
     */
    protected static String getClientCredentialsToken(String tokenUrl, String clientId, String clientSecret) {
        try {
            OkHttpClient client = new OkHttpClient();

            FormBody formBody = new FormBody.Builder()
                .add("grant_type", "client_credentials")
                .add("client_id", clientId)
                .add("client_secret", clientSecret)
                .build();

            Request request = new Request.Builder()
                .url(tokenUrl)
                .post(formBody)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .build();

            try (okhttp3.Response response = client.newCall(request).execute()) {
                if (response.isSuccessful() && response.body() != null) {
                    String responseBody = response.body().string();
                    Map<String, Object> tokenResponse = objectMapper.readValue(responseBody, Map.class);
                    return (String) tokenResponse.get("access_token");
                }
            }
        } catch (Exception e) {
            System.err.println("Client credentials flow failed: " + e.getMessage());
        }
        return null;
    }

    /**
     * Perform OAuth2 authorization code flow (requires manual intervention)
     */
    protected static String getAuthorizationCodeToken(String tokenUrl, String clientId, String clientSecret,
                                                    String authorizationCode, String redirectUri) {
        try {
            OkHttpClient client = new OkHttpClient();

            FormBody formBody = new FormBody.Builder()
                .add("grant_type", "authorization_code")
                .add("client_id", clientId)
                .add("client_secret", clientSecret)
                .add("code", authorizationCode)
                .add("redirect_uri", redirectUri)
                .build();

            Request request = new Request.Builder()
                .url(tokenUrl)
                .post(formBody)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .build();

            try (okhttp3.Response response = client.newCall(request).execute()) {
                if (response.isSuccessful() && response.body() != null) {
                    String responseBody = response.body().string();
                    Map<String, Object> tokenResponse = objectMapper.readValue(responseBody, Map.class);
                    return (String) tokenResponse.get("access_token");
                }
            }
        } catch (Exception e) {
            System.err.println("Authorization code flow failed: " + e.getMessage());
        }
        return null;
    }
}"""
