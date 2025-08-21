#!/usr/bin/env node
/**
 * Node.js API Test Runner
 * Generated from: Simple API overview
 * 
 * This test suite uses shared JSON test data for cross-platform compatibility.
 */

const fs = require('fs');
const axios = require('axios');
const path = require('path');

class APITestRunner {
    /**
     * Test runner for API endpoints using shared JSON test data
     * @param {string} baseUrl - Base URL for the API
     * @param {string} apiKey - Optional API key for authentication
     * @param {Object} oauthConfig - Optional OAuth configuration
     */
    constructor(baseUrl, apiKey = null, oauthConfig = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.oauthConfig = oauthConfig;
        this.testData = null;
        this.accessToken = null;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
        
        // Setup authentication
        this.setupAuth();
    }
    
    setupAuth() {
        if (this.apiKey) {
            this.defaultHeaders['api_key'] = this.apiKey;
        }
        
        if (this.oauthConfig) {
            this.setupOAuth();
        }
    }
    
    async setupOAuth() {
        if (!this.oauthConfig) return;
        
        try {
            // Try password grant first
            if (this.oauthConfig.username && this.oauthConfig.password && this.oauthConfig.client_id) {
                this.accessToken = await this.getOAuthPasswordToken();
            }
            // Try client credentials
            else if (this.oauthConfig.client_id && this.oauthConfig.client_secret) {
                this.accessToken = await this.getOAuthClientCredentialsToken();
            }
            
            if (this.accessToken) {
                this.defaultHeaders['Authorization'] = `Bearer ${this.accessToken}`;
            }
        } catch (error) {
            console.warn(`Warning: OAuth setup failed: ${error.message}`);
        }
    }
    
    async getOAuthPasswordToken() {
        const tokenUrl = `${this.baseUrl}/oauth/token`;
        const data = {
            grant_type: 'password',
            username: this.oauthConfig.username,
            password: this.oauthConfig.password,
            client_id: this.oauthConfig.client_id
        };
        
        try {
            const response = await axios.post(tokenUrl, data);
            return response.data.access_token;
        } catch (error) {
            console.warn(`OAuth password grant failed: ${error.message}`);
            return null;
        }
    }
    
    async getOAuthClientCredentialsToken() {
        const tokenUrl = `${this.baseUrl}/oauth/token`;
        const data = {
            grant_type: 'client_credentials',
            client_id: this.oauthConfig.client_id,
            client_secret: this.oauthConfig.client_secret
        };
        
        try {
            const response = await axios.post(tokenUrl, data);
            return response.data.access_token;
        } catch (error) {
            console.warn(`OAuth client credentials failed: ${error.message}`);
            return null;
        }
    }
    
    loadTestData(jsonFile = 'test-data.json') {
        try {
            const data = fs.readFileSync(jsonFile, 'utf8');
            this.testData = JSON.parse(data);
            console.log(`✅ Loaded ${this.testData.metadata.total_cases} test cases`);
        } catch (error) {
            console.error(`❌ Error loading test data: ${error.message}`);
            process.exit(1);
        }
    }
    
    async runTestCase(testCase) {
        const method = testCase.method.toLowerCase();
        let url = `${this.baseUrl}${testCase.path}`;
        
        // Apply path parameters
        const pathParams = testCase.path_params || {};
        for (const [key, value] of Object.entries(pathParams)) {
            url = url.replace(`${{key}}`, value);
        }
        
        // Prepare request configuration
        const config = {
            method: method,
            url: url,
            headers: {
                ...this.defaultHeaders,
                ...testCase.headers
            },
            params: testCase.query_params || {},
            validateStatus: () => true // Don't throw on HTTP error status
        };
        
        // Add body for POST/PUT requests
        if (testCase.body) {
            config.data = testCase.body;
        }
        
        try {
            const response = await axios(config);
            
            if (response.status === testCase.expected_status) {
                console.log(`✅ ${testCase.name} - PASSED`);
                return true;
            } else {
                console.log(`❌ ${testCase.name} - FAILED: Expected ${testCase.expected_status}, got ${response.status}`);
                if (response.data) {
                    console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}...`);
                }
                return false;
            }
        } catch (error) {
            console.log(`❌ ${testCase.name} - ERROR: ${error.message}`);
            return false;
        }
    }
    
    async runAllTests() {
        if (!this.testData) {
            console.error('❌ No test data loaded. Call loadTestData() first.');
            return { passed: 0, failed: 0 };
        }
        
        console.log(`🧪 Running ${this.testData.metadata.total_cases} test cases...`);
        console.log(`📊 Generated by: ${this.testData.metadata.generator}`);
        console.log(`🔗 Target URL: ${this.baseUrl}`);
        console.log('-'.repeat(50));
        
        let passed = 0;
        let failed = 0;
        
        for (const testCase of this.testData.test_cases) {
            if (await this.runTestCase(testCase)) {
                passed++;
            } else {
                failed++;
            }
        }
        
        console.log('-'.repeat(50));
        console.log(`📈 Results: ${passed} passed, ${failed} failed`);
        
        return { passed, failed };
    }
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length < 1) {
        console.log('Usage: node test_api.js <base_url> [api_key] [oauth_config_file]');
        console.log('');
        console.log('Examples:');
        console.log('  node test_api.js http://localhost:8080');
        console.log('  node test_api.js http://localhost:8080 your-api-key');
        console.log('  node test_api.js http://localhost:8080 your-api-key oauth.json');
        process.exit(1);
    }
    
    const baseUrl = args[0];
    const apiKey = args[1] || null;
    let oauthConfig = null;
    
    // Load OAuth config if provided
    if (args.length > 2) {
        try {
            const oauthData = fs.readFileSync(args[2], 'utf8');
            oauthConfig = JSON.parse(oauthData);
        } catch (error) {
            console.warn(`Warning: Could not load OAuth config: ${error.message}`);
        }
    }
    
    // Create test runner
    const runner = new APITestRunner(baseUrl, apiKey, oauthConfig);
    
    // Load test data
    runner.loadTestData();
    
    // Run tests
    const results = await runner.runAllTests();
    
    // Exit with appropriate code
    if (results.failed > 0) {
        process.exit(1);
    }
}

// Run if this file is executed directly
if (require.main === module) {
    main().catch(error => {
        console.error('Unexpected error:', error);
        process.exit(1);
    });
}
