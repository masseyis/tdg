#!/usr/bin/env python3
"""Test AI provider configuration"""

import pytest
import os
from app.ai.base import get_provider
from app.config import settings

def test_providers():
    print("🔍 Testing AI Provider Configuration")
    print("=" * 50)
    
    # Check environment variables
    print(f"OpenAI API Key: {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
    print(f"Anthropic API Key: {'✅ Set' if settings.anthropic_api_key else '❌ Not set'}")
    print()
    
    # Test provider detection
    provider = get_provider()
    print(f"Auto-detected provider: {provider.__class__.__name__}")
    print(f"Provider available: {'✅ Yes' if provider.is_available() else '❌ No'}")
    print()
    
    # Test specific providers
    from app.ai.openai_provider import OpenAIProvider
    from app.ai.anthropic_provider import AnthropicProvider
    from app.ai.null_provider import NullProvider
    
    openai_provider = OpenAIProvider()
    anthropic_provider = AnthropicProvider()
    null_provider = NullProvider()
    
    print("Provider Status:")
    print(f"  OpenAI: {'✅ Available' if openai_provider.is_available() else '❌ Not available'}")
    print(f"  Anthropic: {'✅ Available' if anthropic_provider.is_available() else '❌ Not available'}")
    print(f"  Null: {'✅ Available' if null_provider.is_available() else '❌ Not available'}")
    print()
    
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("💡 To use AI providers, set your API keys in .env file:")
        print("   OPENAI_API_KEY=sk-your-actual-key")
        print("   ANTHROPIC_API_KEY=sk-ant-your-actual-key")

if __name__ == "__main__":
    test_providers()
