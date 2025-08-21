"""Renderer tests"""
import json
from app.ai.base import TestCase
from app.generation.renderers import junit_restassured, postman, wiremock, csv_renderer


def test_junit_renderer():
    """Test JUnit renderer"""
    cases = [
        TestCase(
            name="test_get_user",
            description="Test getting user",
            method="GET",
            path="/users/123",
            headers={"Accept": "application/json"},
            query_params={},
            path_params={"id": 123},
            body=None,
            expected_status=200,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    api = type('obj', (object,), {
        'title': 'Test API',
        'version': '1.0.0',
        'servers': ['http://localhost:8080']
    })()
    
    files = junit_restassured.render(cases, api)
    
    assert "BaseTest.java" in str(files.keys())
    assert len(files) > 0
    
    # Check generated code contains expected elements
    for content in files.values():
        if "BaseTest" not in content:
            assert "ParameterizedTest" in content
            assert "test_get_user" in content


def test_postman_renderer():
    """Test Postman collection renderer"""
    cases = [
        TestCase(
            name="Create User",
            description="Test creating user",
            method="POST",
            path="/users",
            headers={"Content-Type": "application/json"},
            query_params={},
            path_params={},
            body={"name": "John", "email": "john@example.com"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    api = type('obj', (object,), {
        'title': 'Test API',
        'version': '1.0.0',
        'description': 'Test API',
        'servers': ['http://localhost:8080']
    })()
    
    collection = postman.render(cases, api)
    
    assert collection["info"]["name"] == "Test API"
    assert len(collection["item"]) > 0
    assert collection["variable"][0]["key"] == "baseUrl"


def test_csv_renderer():
    """Test CSV renderer"""
    cases = [
        TestCase(
            name="test1",
            description="Test 1",
            method="GET",
            path="/test",
            headers={},
            query_params={"page": 1},
            path_params={},
            body={"data": "test"},
            expected_status=200,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    csv_output = csv_renderer.render(cases)
    
    assert "name,method,path" in csv_output.replace(" ", "")
    assert "test1" in csv_output
    assert "GET" in csv_output