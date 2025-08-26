"""OpenAI provider for test case generation"""

import json
import logging
from typing import Any, Dict, List

from app.ai.base import AIProvider, TestCase
from app.ai.prompts import get_test_generation_prompt, order_test_cases
from app.config import settings
from app.utils.json_repair import extract_json_from_content, safe_json_parse

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI provider for test case generation"""

    def __init__(self):
        self.client = None
        if self.is_available():
            try:
                import openai

                self.client = openai.OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI library not installed")

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(settings.openai_api_key)

    def _get_model_config(self, speed: str, endpoint: Any = None) -> tuple[str, float, int]:
        """Get model configuration based on speed preference and endpoint type"""
        if speed == "fast":
            # Allocate more tokens for POST operations to ensure rich data generation
            tokens = 2000 if (endpoint and endpoint.method == "POST") else 1000
            return "gpt-4o-mini", 0.5, tokens  # Slightly higher temperature for more variety
        elif speed == "balanced":
            return settings.openai_model, settings.ai_temperature, settings.ai_max_tokens
        elif speed == "quality":
            return "gpt-4o", 0.7, 3000  # Best quality model, higher temperature, more tokens
        else:
            return settings.openai_model, settings.ai_temperature, settings.ai_max_tokens

    async def generate_cases(self, endpoint: Any, options: Dict[str, Any]) -> List[TestCase]:
        """Generate test cases using OpenAI"""
        if not self.client:
            # Fallback to null provider
            from app.ai.null_provider import NullProvider

            return await NullProvider().generate_cases(endpoint, options)

        try:
            prompt = get_test_generation_prompt(endpoint, options)

            # Get model configuration based on speed preference and endpoint type
            speed = options.get("speed", "fast")
            model, temperature, max_tokens = self._get_model_config(speed, endpoint)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test data generation expert. "
                        "Generate test cases as valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                timeout=settings.ai_timeout,
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
                    test_type=case_data.get("test_type", "valid"),
                )
                cases.append(case)

            # Order test cases logically: CREATE → READ → UPDATE → DELETE
            ordered_cases = order_test_cases(cases)

            return ordered_cases

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            # Fallback to null provider
            from app.ai.null_provider import NullProvider

            return await NullProvider().generate_cases(endpoint, options)

    async def _call_ai(self, prompt: str) -> str:
        """
        Call OpenAI API with a custom prompt and return the response
        
        Args:
            prompt: The prompt to send to OpenAI
            
        Returns:
            The AI response as a string
        """
        if not self.client:
            raise Exception("OpenAI client not available")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use fast model for enhancement
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test data generation expert. Generate test cases as valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent enhancement
                max_tokens=1500,  # Reasonable limit for enhancement
                timeout=30,  # Shorter timeout for enhancement
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
