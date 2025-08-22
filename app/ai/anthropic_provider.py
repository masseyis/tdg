"""Anthropic AI provider"""
import json
import logging
from typing import List, Dict, Any
from app.ai.base import AIProvider, TestCase
from app.ai.prompts import get_test_generation_prompt, order_test_cases
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
            return "claude-3-haiku-20240307", 0.3, 1000  # Fastest model, lower temperature, fewer tokens
        elif speed == "balanced":
            return settings.anthropic_model, settings.ai_temperature, settings.ai_max_tokens
        elif speed == "quality":
            return "claude-3-opus-20240229", 0.7, 3000  # Best quality model, higher temperature, more tokens
        else:
            return settings.anthropic_model, settings.ai_temperature, settings.ai_max_tokens

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
                system="You are a test data generation expert. "
                       "Generate test cases as valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract JSON from response
            content = message.content[0].text
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                content = content[json_start:json_end]

            data = json.loads(content)

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
