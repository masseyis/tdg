"""Tests for the hybrid AI provider"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.hybrid_provider import HybridProvider
from app.ai.base import TestCase


@pytest.fixture
def mock_endpoint():
    """Mock endpoint for testing"""
    endpoint = MagicMock()
    endpoint.method = "POST"
    endpoint.path = "/pets"
    endpoint.summary = "Create a new pet"
    return endpoint


@pytest.fixture
def mock_options():
    """Mock options for testing"""
    return {
        "cases_per_endpoint": 3,
        "domain_hint": "petstore",
        "speed": "fast"
    }


@pytest.mark.asyncio
async def test_hybrid_provider_initialization():
    """Test that hybrid provider initializes correctly"""
    provider = HybridProvider()
    
    # Should always be available (falls back to null)
    assert provider.is_available() is True
    
    # Should have null provider
    assert provider.null_provider is not None
    
    # May or may not have AI provider depending on API keys
    # This is expected behavior


@pytest.mark.asyncio
async def test_hybrid_provider_without_ai(mock_endpoint, mock_options):
    """Test hybrid provider when no AI provider is available"""
    with patch('app.ai.openai_provider.OpenAIProvider.is_available', return_value=False), \
         patch('app.ai.fast_provider.FastAIProvider.is_available', return_value=False), \
         patch('app.ai.anthropic_provider.AnthropicProvider.is_available', return_value=False):
        
        provider = HybridProvider()
        
        # Should fall back to null provider only
        cases = await provider.generate_cases(mock_endpoint, mock_options)
        
        # Should get some cases from null provider
        assert len(cases) > 0
        assert all(isinstance(case, TestCase) for case in cases)


@pytest.mark.asyncio
async def test_hybrid_provider_with_ai(mock_endpoint, mock_options):
    """Test hybrid provider with AI enhancement"""
    provider = HybridProvider()
    
    # Mock foundation cases from null provider
    foundation_cases = [
        TestCase(
            name="Basic test case",
            description="A basic test case",
            method="POST",
            path="/pets",
            headers={},
            query_params={},
            path_params={},
            body={"name": "test", "species": "dog"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    # Mock AI response
    mock_ai_response = '''
```json
[
  {
    "name": "Test with domain-specific valid data",
    "method": "POST",
    "path": "/pets",
    "test_type": "valid",
    "expected_status": 201,
    "body": {"name": "Buddy", "species": "dog", "age": 3},
    "query_params": {},
    "path_params": {},
    "headers": {"Content-Type": "application/json"}
  },
  {
    "name": "Test boundary case - maximum age",
    "method": "POST",
    "path": "/pets",
    "test_type": "boundary",
    "expected_status": 400,
    "body": {"name": "Old Dog", "species": "dog", "age": 999},
    "query_params": {},
    "path_params": {},
    "headers": {"Content-Type": "application/json"}
  }
]
```
'''
    
    # Mock the AI provider to return our response
    with patch.object(provider.null_provider, 'generate_cases', return_value=foundation_cases), \
         patch.object(provider, 'ai_provider') as mock_ai_provider:
        
        # Set up the mock AI provider
        mock_ai_provider.is_available.return_value = True
        mock_ai_provider._call_ai = AsyncMock(return_value=mock_ai_response)
        
        # Should use AI provider for enhancement
        cases = await provider.generate_cases(mock_endpoint, mock_options)
        
        # Should have foundation cases + enhanced cases
        assert len(cases) >= 3  # At least 1 foundation + 2 enhanced
        assert all(isinstance(case, TestCase) for case in cases)
        
        # Check that we have both foundation and enhanced cases
        case_names = [case.name for case in cases]
        assert "Basic test case" in case_names  # Foundation case
        
        # Check that we have enhanced cases (AI may generate more than expected)
        enhanced_case_names = [name for name in case_names if name != "Basic test case"]
        assert len(enhanced_case_names) >= 2  # At least 2 enhanced cases


@pytest.mark.asyncio
async def test_hybrid_provider_ai_failure(mock_endpoint, mock_options):
    """Test hybrid provider when AI enhancement fails"""
    provider = HybridProvider()
    
    # Mock foundation cases from null provider
    foundation_cases = [
        TestCase(
            name="Basic test case",
            description="A basic test case",
            method="POST",
            path="/pets",
            headers={},
            query_params={},
            path_params={},
            body={"name": "test", "species": "dog"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    # Mock the AI provider to fail
    with patch.object(provider.null_provider, 'generate_cases', return_value=foundation_cases), \
         patch.object(provider, 'ai_provider') as mock_ai_provider:
        
        # Set up the mock AI provider to fail
        mock_ai_provider.is_available.return_value = True
        mock_ai_provider._call_ai = AsyncMock(side_effect=Exception("AI failed"))
        
        # Should fall back to foundation cases only
        cases = await provider.generate_cases(mock_endpoint, mock_options)
        
        # Should still have foundation cases
        assert len(cases) == 1
        assert cases[0].name == "Basic test case"


@pytest.mark.asyncio
async def test_hybrid_provider_invalid_json(mock_endpoint, mock_options):
    """Test hybrid provider when AI returns invalid JSON"""
    provider = HybridProvider()
    
    # Mock foundation cases from null provider
    foundation_cases = [
        TestCase(
            name="Basic test case",
            description="A basic test case",
            method="POST",
            path="/pets",
            headers={},
            query_params={},
            path_params={},
            body={"name": "test", "species": "dog"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    # Mock invalid AI response
    mock_ai_response = "This is not valid JSON"
    
    # Mock the AI provider to return our invalid response
    with patch.object(provider.null_provider, 'generate_cases', return_value=foundation_cases), \
         patch.object(provider, 'ai_provider') as mock_ai_provider:
        
        # Set up the mock AI provider
        mock_ai_provider.is_available.return_value = True
        mock_ai_provider._call_ai = AsyncMock(return_value=mock_ai_response)
        
        # Should fall back to foundation cases only
        cases = await provider.generate_cases(mock_endpoint, mock_options)
        
        # Should still have foundation cases
        assert len(cases) == 1
        assert cases[0].name == "Basic test case"


def test_enhancement_prompt_building(mock_endpoint):
    """Test that enhancement prompt is built correctly"""
    provider = HybridProvider()
    
    foundation_cases = [
        TestCase(
            name="Basic test case",
            description="A basic test case",
            method="POST",
            path="/pets",
            headers={},
            query_params={},
            path_params={},
            body={"name": "test", "species": "dog"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    prompt = provider._build_enhancement_prompt(foundation_cases, mock_endpoint, "petstore")
    
    # Should contain endpoint details
    assert "POST" in prompt
    assert "/pets" in prompt
    assert "petstore" in prompt
    
    # Should contain foundation cases
    assert "Basic test case" in prompt
    assert "test" in prompt  # body content
    
    # Should contain task instructions
    assert "Domain-Specific Values" in prompt
    assert "Boundary Cases" in prompt
    assert "Negative Cases" in prompt


def test_parse_enhanced_cases():
    """Test parsing of enhanced cases from AI response"""
    provider = HybridProvider()
    
    mock_endpoint = MagicMock()
    mock_endpoint.method = "POST"
    mock_endpoint.path = "/pets"
    
    # Valid JSON response
    ai_response = '''
```json
[
  {
    "name": "Test with domain-specific valid data",
    "method": "POST",
    "path": "/pets",
    "test_type": "valid",
    "expected_status": 201,
    "body": {"name": "Buddy", "species": "dog", "age": 3},
    "query_params": {},
    "path_params": {},
    "headers": {"Content-Type": "application/json"}
  }
]
```
'''
    
    cases = provider._parse_enhanced_cases(ai_response, mock_endpoint)
    
    assert len(cases) == 1
    case = cases[0]
    assert case.name == "Test with domain-specific valid data"
    assert case.method == "POST"
    assert case.path == "/pets"
    assert case.test_type == "valid"
    assert case.expected_status == 201
    assert case.body == {"name": "Buddy", "species": "dog", "age": 3}
