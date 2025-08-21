package generated;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.Map;
import java.util.List;
import java.util.stream.Stream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;

public class PutPetTest extends BaseTest {

    private static JsonNode testData;
    private static ObjectMapper objectMapper = new ObjectMapper();

    @BeforeAll
    static void loadTestData() throws Exception {
        InputStream inputStream = PutPetTest.class.getClassLoader()
            .getResourceAsStream("test-data.json");
        if (inputStream == null) {
            throw new RuntimeException("test-data.json not found in resources");
        }
        String json = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
        testData = objectMapper.readTree(json);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("provideTestCases")
    void testEndpoint(String testCaseId) {
        // Find the test case by ID
        JsonNode testCase = null;
        for (JsonNode tc : testData.get("test_cases")) {
            if (testCaseId.equals(tc.get("id").asText())) {
                testCase = tc;
                break;
            }
        }
        
        if (testCase == null) {
            fail("Test case not found: " + testCaseId);
            return;
        }
        
        String method = testCase.get("method").asText();
        String path = testCase.get("path").asText();
        JsonNode bodyNode = testCase.get("body");
        JsonNode queryParamsNode = testCase.get("query_params");
        JsonNode pathParamsNode = testCase.get("path_params");
        int expectedStatus = testCase.get("expected_status").asInt();
        var request = given()
            .contentType(ContentType.JSON)
            .accept(ContentType.JSON);

        // Add OAuth2 authentication headers if available
        Map<String, String> authHeaders = getAuthHeaders();
        for (Map.Entry<String, String> header : authHeaders.entrySet()) {
            request.header(header.getKey(), header.getValue());
        }

        // Add custom headers from test data
        JsonNode headersNode = testCase.get("headers");
        if (headersNode != null && headersNode.isObject()) {
            headersNode.fields().forEachRemaining(entry -> {
                request.header(entry.getKey(), entry.getValue().asText());
            });
        }

        // Add query parameters if present
        if (queryParamsNode != null && queryParamsNode.isObject()) {
            queryParamsNode.fields().forEachRemaining(entry -> {
                request.queryParam(entry.getKey(), entry.getValue().asText());
            });
        }

        // Add path parameters if present
        if (pathParamsNode != null && pathParamsNode.isObject()) {
            pathParamsNode.fields().forEachRemaining(entry -> {
                request.pathParam(entry.getKey(), entry.getValue().asText());
            });
        }

        // Add body if present
        if (bodyNode != null && !bodyNode.isNull()) {
            request.body(bodyNode.toString());
        }

        var response = request.request(method, path);

        response.then()
            .statusCode(expectedStatus);
    }

    static Stream<Arguments> provideTestCases() {
        return Stream.of(
            Arguments.of("Valid_updatePet_0"),
            Arguments.of("Valid_updatePet_1"),
            Arguments.of("Boundary_updatePet_0"),
            Arguments.of("Negative_updatePet_0"),
            Arguments.of("Negative_updatePet_1")
        );
    }
}