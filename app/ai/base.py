"""Base AI provider interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.progress import ProgressCallback


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
        options: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[TestCase]:
        """
        Generate test cases for an endpoint

        Args:
            endpoint: Normalized endpoint
            options: Generation options (count, domain_hint, seed, etc.)
            progress_callback: Optional progress callback for reporting progress

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
        provider_name: Provider name (null, openai, anthropic, fast, hybrid)

    Returns:
        AI provider instance
    """
    from app.ai.anthropic_provider import AnthropicProvider
    from app.ai.fast_provider import FastAIProvider
    from app.ai.hybrid_provider import HybridProvider
    from app.ai.null_provider import NullProvider
    from app.ai.openai_provider import OpenAIProvider

    providers = {
        "null": NullProvider(),
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "fast": FastAIProvider(),
        "hybrid": HybridProvider(),
    }

    # Auto-detect if not specified
    if not provider_name:
        # Try hybrid provider first (best of both worlds)
        if providers["hybrid"].is_available():
            return providers["hybrid"]
        # Then try fast provider for speed
        if providers["fast"].is_available():
            return providers["fast"]
        # Then try other providers
        for name, provider in providers.items():
            if name not in ["null", "fast", "hybrid"] and provider.is_available():
                return provider
        return providers["null"]

    return providers.get(provider_name, providers["null"])


def get_provider_for_speed(speed: str) -> AIProvider:
    """
    Get AI provider optimized for the specified speed preference

    Args:
        speed: Speed preference (fast, balanced, quality)

    Returns:
        AI provider instance optimized for speed
    """
    from app.ai.anthropic_provider import AnthropicProvider
    from app.ai.fast_provider import FastAIProvider
    from app.ai.hybrid_provider import HybridProvider
    from app.ai.null_provider import NullProvider
    from app.ai.openai_provider import OpenAIProvider

    providers = {
        "null": NullProvider(),
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "fast": FastAIProvider(),
        "hybrid": HybridProvider(),
    }

    if speed == "fast":
        # Use hybrid provider first (fast foundation + AI enhancement)
        if providers["hybrid"].is_available():
            return providers["hybrid"]
        # Use fast provider if available, otherwise fastest available
        if providers["fast"].is_available():
            return providers["fast"]
        # Try OpenAI with gpt-4o-mini
        if providers["openai"].is_available():
            return providers["openai"]
        # Try Anthropic with haiku
        if providers["anthropic"].is_available():
            return providers["anthropic"]

    elif speed == "balanced":
        # Use hybrid provider for balanced approach
        if providers["hybrid"].is_available():
            return providers["hybrid"]
        # Use balanced models
        if providers["openai"].is_available():
            return providers["openai"]
        if providers["anthropic"].is_available():
            return providers["anthropic"]
        if providers["fast"].is_available():
            return providers["fast"]

    elif speed == "quality":
        # Use hybrid provider for quality (foundation + AI enhancement)
        if providers["hybrid"].is_available():
            return providers["hybrid"]
        # Use highest quality models
        if providers["openai"].is_available():
            return providers["openai"]
        if providers["anthropic"].is_available():
            return providers["anthropic"]
        if providers["fast"].is_available():
            return providers["fast"]

    # Fallback to null provider
    return providers["null"]
