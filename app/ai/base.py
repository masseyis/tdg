"""Base AI provider interface"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass

class TestCase:
    """Generated test case"""
    name: str
    description: Optional[str]
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    path_params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    expected_status: int
    expected_response: Optional[Dict[str, Any]]
    test_type: str  # valid, boundary, negative


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def generate_cases(
        self,
        endpoint: Any,
        options: Dict[str, Any]
    ) -> List[TestCase]:
        """
        Generate test cases for an endpoint

        Args:
            endpoint: Normalized endpoint
            options: Generation options (count, domain_hint, seed, etc.)

        Returns:
            List of generated test cases
        """
        pass

    @abstractmethod

    def is_available(self) -> bool:
        """Check if provider is available (has API key, etc.)"""
        pass


def get_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Get AI provider instance

    Args:
        provider_name: Provider name (null, openai, anthropic)

    Returns:
        AI provider instance
    """
    from app.ai.null_provider import NullProvider
    from app.ai.openai_provider import OpenAIProvider
    from app.ai.anthropic_provider import AnthropicProvider

    providers = {
        "null": NullProvider(),
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider()
    }

    # Auto-detect if not specified
    if not provider_name:
        for name, provider in providers.items():
            if name != "null" and provider.is_available():
                return provider
        return providers["null"]

    return providers.get(provider_name, providers["null"])
