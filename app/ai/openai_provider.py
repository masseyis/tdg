import json
import logging
from typing import List, Dict, Any
from app.ai.base import AIProvider, TestCase
from app.ai.prompts import get_test_generation_prompt
from app.config import settings

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

    async def generate_cases(
        self,
        endpoint: Any,
        options: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate test cases using OpenAI"""
        if not self.client:
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)

        try:
            prompt = get_test_generation_prompt(endpoint, options)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test data generation expert. "
                                                  "Generate test cases as valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
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

            return cases

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            # Fallback to null provider
            from app.ai.null_provider import NullProvider
            return await NullProvider().generate_cases(endpoint, options)
