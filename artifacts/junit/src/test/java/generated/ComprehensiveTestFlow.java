package generated;

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
}}