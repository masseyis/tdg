"""Fast AI provider for quick test generation"""
import json
import logging
from typing import List, Dict, Any
from app.ai.base import AIProvider, TestCase
from app.ai.prompts import get_test_generation_prompt, order_test_cases
from app.utils.json_repair import safe_json_parse, extract_json_from_content
from app.config import settings

logger = logging.getLogger(__name__)


class FastAIProvider(AIProvider):
    """Fast AI provider that prioritizes speed over quality for quick generation"""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._setup_clients()

    def _setup_clients(self):
        """Setup AI clients with fastest models"""
        if settings.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI library not installed")
        
        if settings.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                logger.warning("Anthropic library not installed")

    def is_available(self) -> bool:
        """Check if any fast AI provider is available"""
        return bool(self.openai_client or self.anthropic_client)

    async def generate_cases(
        self,
        endpoint: Any,
        options: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate test cases using the fastest available AI model"""
        
        # Try OpenAI first (gpt-4o-mini is fastest)
        if self.openai_client:
            try:
                return await self._generate_with_openai(endpoint, options)
            except Exception as e:
                logger.warning(f"OpenAI fast generation failed: {e}")
        
        # Try Anthropic (haiku is fastest)
        if self.anthropic_client:
            try:
                return await self._generate_with_anthropic(endpoint, options)
            except Exception as e:
                logger.warning(f"Anthropic fast generation failed: {e}")
        
        # Fallback to null provider
        from app.ai.null_provider import NullProvider
        return await NullProvider().generate_cases(endpoint, options)

    async def _generate_with_openai(self, endpoint: Any, options: Dict[str, Any]) -> List[TestCase]:
        """Generate using OpenAI with fastest settings"""
        prompt = get_test_generation_prompt(endpoint, options)

        # Allocate more tokens for POST operations to ensure rich data generation
        max_tokens = 2000 if endpoint.method == "POST" else 1000
        timeout = 60 if endpoint.method == "POST" else 45  # Increased timeouts for better reliability

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fastest OpenAI model
            messages=[
                {"role": "system", "content": "Generate test cases as valid JSON with rich, meaningful data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Slightly higher temperature for more variety
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            timeout=timeout
        )

        content = response.choices[0].message.content
        
        # Use JSON repair utility for robust parsing
        data = safe_json_parse(content)
        if not data:
            logger.warning("OpenAI returned invalid JSON, attempting extraction...")
            # Try to extract and repair JSON from the response
            data = extract_json_from_content(content)
            
        if not data:
            logger.error("Failed to extract valid JSON from OpenAI response")
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)
        
        return self._parse_cases(data, endpoint)

    async def _generate_with_anthropic(self, endpoint: Any, options: Dict[str, Any]) -> List[TestCase]:
        """Generate using Anthropic with fastest settings"""
        prompt = get_test_generation_prompt(endpoint, options)

        # Allocate more tokens for POST operations to ensure rich data generation
        max_tokens = 2000 if endpoint.method == "POST" else 1000

        message = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",  # Fastest Anthropic model
            max_tokens=max_tokens,
            temperature=0.5,  # Slightly higher temperature for more variety
            system="Generate test cases as valid JSON with rich, meaningful data.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract JSON from response
        content = message.content[0].text
        
        # Use JSON repair utility for robust parsing
        data = safe_json_parse(content)
        if not data:
            logger.warning("Anthropic returned invalid JSON, attempting extraction...")
            # Try to extract and repair JSON from the response
            data = extract_json_from_content(content)
            
        if not data:
            logger.error("Failed to extract valid JSON from Anthropic response")
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)
        
        return self._parse_cases(data, endpoint)

    def _parse_cases(self, data: Dict[str, Any], endpoint: Any) -> List[TestCase]:
        """Parse response into TestCase objects"""
        cases = []
        for case_data in data.get("cases", []):
            case = TestCase(
                name=case_data.get("name", "test_case"),
                description=case_data.get("description"),
                method=endpoint.method,
                path=endpoint.path,
                headers=case_data.get("headers", {}),
                query_params=case_data.get("query_params", {}),
                path_params=case_data.get("path_params", {}),
                body=case_data.get("body"),
                expected_status=case_data.get("expected_status", 200),
                expected_response=case_data.get("expected_response"),
                test_type=case_data.get("test_type", "valid")
            )
            cases.append(case)

        # Order test cases logically: CREATE → READ → UPDATE → DELETE
        return order_test_cases(cases)
