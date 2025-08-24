"""Anthropic AI provider"""
import json
import logging
from typing import List, Dict, Any
from app.ai.base import AIProvider, TestCase
from app.ai.prompts import get_test_generation_prompt, order_test_cases
from app.utils.json_repair import safe_json_parse, extract_json_from_content
from app.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic provider for test case generation"""

    def __init__(self):
        self.client = None
        if self.is_available():
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                logger.warning("Anthropic library not installed")

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured"""
        return bool(settings.anthropic_api_key)

    def _get_model_config(self, speed: str) -> tuple[str, float, int]:
        """Get model configuration based on speed preference"""
        if speed == "fast":
            return "claude-3-haiku-20240307", 0.5, 1500  # Fastest model
        elif speed == "balanced":
            return "claude-3-sonnet-20240229", 0.3, 2000  # Balanced model
        elif speed == "quality":
            return "claude-3-opus-20240229", 0.7, 3000  # Best quality model
        else:
            return "claude-3-sonnet-20240229", 0.3, 2000  # Default to balanced

    async def generate_cases(
        self,
        endpoint: Any,
        options: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate test cases using Anthropic"""
        if not self.client:
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)

        try:
            prompt = get_test_generation_prompt(endpoint, options)

            # Get model configuration based on speed preference
            speed = options.get("speed", "fast")
            model, temperature, max_tokens = self._get_model_config(speed)
            
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are a test data generation expert. Generate test cases as valid JSON with rich, meaningful data.",
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

            # Parse response into TestCase objects
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
            ordered_cases = order_test_cases(cases)

            return ordered_cases

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)
