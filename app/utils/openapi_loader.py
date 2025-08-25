"""Load OpenAPI specs from various sources"""

import base64
import json
import logging
from typing import Any, Dict

import httpx
import yaml

logger = logging.getLogger(__name__)


async def load_openapi_spec(source: str) -> Dict[str, Any]:
    """
    Load OpenAPI spec from base64 content or URL

    Args:
        source: Base64 encoded content or URL

    Returns:
        Parsed OpenAPI specification
    """
    try:
        # Try URL first
        if source.startswith(("http://", "https://")):
            return await load_from_url(source)

        # Try base64 decode
        try:
            decoded = base64.b64decode(source)
            content = decoded.decode("utf-8")
            return parse_spec_content(content)
        except Exception:
            # Maybe it's raw content
            return parse_spec_content(source)

    except Exception as e:
        logger.error(f"Failed to load OpenAPI spec: {e}")
        raise ValueError(f"Invalid OpenAPI source: {e}")


async def load_from_url(url: str) -> Dict[str, Any]:
    """Load OpenAPI spec from URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
        return parse_spec_content(content)


def parse_spec_content(content: str) -> Dict[str, Any]:
    """Parse OpenAPI spec content (JSON or YAML)"""
    # Try JSON first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try YAML
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid OpenAPI spec format: {e}")
