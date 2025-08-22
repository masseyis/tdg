package generated;

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
}