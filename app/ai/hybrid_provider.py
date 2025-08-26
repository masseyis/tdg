"""Hybrid AI provider that combines null provider speed with AI intelligence"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.ai.base import AIProvider, TestCase
from app.ai.null_provider import NullProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.fast_provider import FastAIProvider
from app.ai.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class HybridProvider(AIProvider):
    """
    Hybrid provider that combines null provider speed with AI intelligence.
    
    Strategy:
    1. Use null provider to generate foundation test cases quickly
    2. Send those cases to AI to enhance with domain-specific values
    3. AI adds boundary cases, negative cases, and domain-specific data
    4. Get the best of both worlds: speed + intelligence
    """

    def __init__(self):
        self.null_provider = NullProvider()
        self.ai_providers = [
            FastAIProvider(),
            OpenAIProvider(), 
            AnthropicProvider()
        ]
        self.ai_provider = None
        
        # Find the best available AI provider
        for provider in self.ai_providers:
            if provider.is_available():
                self.ai_provider = provider
                logger.info(f"Using AI provider: {provider.__class__.__name__}")
                break
        
        if not self.ai_provider:
            logger.warning("No AI provider available, falling back to null provider only")

    def is_available(self) -> bool:
        """Hybrid provider is always available (falls back to null)"""
        return True

    async def generate_cases(self, endpoint: Any, options: Dict[str, Any]) -> List[TestCase]:
        """
        Generate test cases using hybrid approach:
        1. Null provider generates foundation cases
        2. AI enhances with domain-specific values and edge cases
        """
        domain_hint = options.get("domain_hint", "")
        cases_per_endpoint = options.get("cases_per_endpoint", 5)
        task_id = options.get("task_id")  # For progress updates
        
        # Safely access endpoint attributes
        method = getattr(endpoint, 'method', 'UNKNOWN')
        path = getattr(endpoint, 'path', 'UNKNOWN')
        
        logger.info(f"🔄 Starting hybrid generation for {path}")
        logger.info(f"   Domain: {domain_hint}, Cases: {cases_per_endpoint}")
        
        # Step 1: Generate foundation cases with null provider
        if task_id:
            from app.main import update_progress
            await update_progress(task_id, "generating", 40, f"Generating foundation cases for {method} {path}...")
        
        logger.info("📝 Step 1: Generating foundation cases with null provider...")
        foundation_cases = await self.null_provider.generate_cases(endpoint, options)
        logger.info(f"✅ Generated {len(foundation_cases)} foundation cases")
        
        if not self.ai_provider:
            logger.warning("⚠️  No AI provider available, returning foundation cases only")
            if task_id:
                await update_progress(task_id, "generating", 80, f"Foundation cases complete ({len(foundation_cases)} cases)")
            return foundation_cases
        
        # Step 2: Enhance with AI
        if task_id:
            # Safely access endpoint attributes
            method = getattr(endpoint, 'method', 'UNKNOWN')
            path = getattr(endpoint, 'path', 'UNKNOWN')
            await update_progress(task_id, "generating", 60, f"Enhancing cases with AI for {method} {path}...")
        
        logger.info("🤖 Step 2: Enhancing cases with AI...")
        enhanced_cases = await self._enhance_with_ai(foundation_cases, endpoint, domain_hint, task_id)
        
        # Combine foundation and enhanced cases
        all_cases = foundation_cases + enhanced_cases
        
        if task_id:
            await update_progress(task_id, "generating", 80, f"Hybrid generation complete: {len(all_cases)} total cases")
        
        logger.info(f"🎉 Hybrid generation complete: {len(all_cases)} total cases")
        
        return all_cases

    async def _enhance_with_ai(self, foundation_cases: List[TestCase], endpoint: Any, domain_hint: str, task_id: str = None) -> List[TestCase]:
        """
        Send foundation cases to AI for enhancement with domain-specific values and edge cases
        """
        try:
            # Prepare the prompt for AI enhancement
            if task_id:
                from app.main import update_progress
                # Safely access endpoint attributes
                method = getattr(endpoint, 'method', 'UNKNOWN')
                path = getattr(endpoint, 'path', 'UNKNOWN')
                await update_progress(task_id, "generating", 65, f"Preparing AI enhancement prompt for {method} {path}...")
            
            prompt = self._build_enhancement_prompt(foundation_cases, endpoint, domain_hint)
            
            # Get AI response
            if task_id:
                method = getattr(endpoint, 'method', 'UNKNOWN')
                path = getattr(endpoint, 'path', 'UNKNOWN')
                await update_progress(task_id, "generating", 70, f"Calling AI for enhancement of {method} {path}...")
            
            response = await self.ai_provider._call_ai(prompt)
            
            # Parse enhanced cases
            if task_id:
                method = getattr(endpoint, 'method', 'UNKNOWN')
                path = getattr(endpoint, 'path', 'UNKNOWN')
                await update_progress(task_id, "generating", 75, f"Parsing AI enhancement results for {method} {path}...")
            
            enhanced_cases = self._parse_enhanced_cases(response, endpoint)
            
            logger.info(f"✅ AI enhanced with {len(enhanced_cases)} additional cases")
            return enhanced_cases
            
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")
            logger.info("🔄 Falling back to foundation cases only")
            
            # Capture AI enhancement errors with Sentry for monitoring
            try:
                from app.sentry import capture_exception
                capture_exception(e, context={"task_id": task_id, "stage": "ai_enhancement"})
            except ImportError:
                pass  # Sentry not available
            
            if task_id:
                from app.main import update_progress
                method = getattr(endpoint, 'method', 'UNKNOWN')
                path = getattr(endpoint, 'path', 'UNKNOWN')
                await update_progress(task_id, "generating", 75, f"AI enhancement failed, using foundation cases only for {method} {path}")
            
            return []

    def _build_enhancement_prompt(self, foundation_cases: List[TestCase], endpoint: Any, domain_hint: str) -> str:
        """
        Build a prompt asking AI to enhance the foundation cases
        """
        # Convert foundation cases to JSON for AI to analyze
        foundation_json = []
        for case in foundation_cases:
            foundation_json.append({
                "name": case.name,
                "method": case.method,
                "path": case.path,
                "test_type": case.test_type,
                "expected_status": case.expected_status,
                "body": case.body,
                "query_params": case.query_params,
                "path_params": case.path_params
            })
        
        # Safely access endpoint attributes
        method = getattr(endpoint, 'method', 'UNKNOWN')
        path = getattr(endpoint, 'path', 'UNKNOWN')
        summary = getattr(endpoint, 'summary', 'N/A')
        
        prompt = f"""
You are an expert test case generator. I have generated some foundation test cases for an API endpoint, and I need you to enhance them with domain-specific values and additional edge cases.

ENDPOINT DETAILS:
- Method: {method}
- Path: {path}
- Domain: {domain_hint or 'General'}
- Description: {summary}

FOUNDATION TEST CASES:
{json.dumps(foundation_json, indent=2)}

TASK:
Please enhance these test cases by:

1. **Domain-Specific Values**: Replace generic values with realistic domain-specific data
2. **Boundary Cases**: Add edge cases testing limits, boundaries, and edge conditions
3. **Negative Cases**: Add cases testing invalid inputs, error conditions, and failure scenarios
4. **Data Quality**: Ensure values are realistic and appropriate for the domain

REQUIREMENTS:
- Generate 2-3 additional enhanced cases
- Focus on quality over quantity
- Make values domain-specific and realistic
- Include boundary and negative test cases
- Maintain the same JSON structure as the foundation cases
- Ensure all cases are valid and testable

RESPONSE FORMAT:
Return ONLY a valid JSON array of enhanced test cases. Each case should have:
- name: Descriptive test name
- method: HTTP method
- path: API path
- test_type: "valid", "boundary", or "negative"
- expected_status: Expected HTTP status code
- body: Request body (if applicable)
- query_params: Query parameters (if applicable)
- path_params: Path parameters (if applicable)
- headers: Request headers (if applicable)

Example response:
```json
[
  {{
    "name": "Test with domain-specific valid data",
    "method": "POST",
    "path": "/pets",
    "test_type": "valid",
    "expected_status": 201,
    "body": {{"name": "Buddy", "species": "dog", "age": 3}},
    "query_params": {{}},
    "path_params": {{}},
    "headers": {{"Content-Type": "application/json"}}
  }},
  {{
    "name": "Test boundary case - maximum age",
    "method": "POST", 
    "path": "/pets",
    "test_type": "boundary",
    "expected_status": 400,
    "body": {{"name": "Old Dog", "species": "dog", "age": 999}},
    "query_params": {{}},
    "path_params": {{}},
    "headers": {{"Content-Type": "application/json"}}
  }}
]
```

Generate enhanced test cases now:
"""
        return prompt

    def _parse_enhanced_cases(self, ai_response: str, endpoint: Any) -> List[TestCase]:
        """
        Parse the AI response into TestCase objects
        """
        try:
            # Extract JSON from AI response
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON array found in AI response")
                return []
            
            json_str = ai_response[json_start:json_end]
            enhanced_data = json.loads(json_str)
            
            # Convert to TestCase objects
            enhanced_cases = []
            for case_data in enhanced_data:
                # Safely access endpoint attributes
                method = getattr(endpoint, 'method', 'UNKNOWN')
                path = getattr(endpoint, 'path', 'UNKNOWN')
                
                case = TestCase(
                    name=case_data.get("name", "Enhanced Test Case"),
                    description=None,
                    method=case_data.get("method", method),
                    path=case_data.get("path", path),
                    headers=case_data.get("headers", {}),
                    query_params=case_data.get("query_params", {}),
                    path_params=case_data.get("path_params", {}),
                    body=case_data.get("body"),
                    expected_status=case_data.get("expected_status", 200),
                    expected_response=None,
                    test_type=case_data.get("test_type", "valid")
                )
                enhanced_cases.append(case)
            
            return enhanced_cases
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"AI Response: {ai_response}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse enhanced cases: {e}")
            return []
