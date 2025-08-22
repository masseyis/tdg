"""Test case generation orchestration"""
import logging
from typing import Dict, Any, List
from app.ai.base import get_provider, get_provider_for_speed
from app.utils.validation import validate_against_schema, fix_data_for_schema
from app.utils.flows import create_basic_flows
from app.generation.renderers import (
    junit_restassured,
    postman,
    wiremock,
    csv_renderer,
    sql_renderer,
    json_renderer,
    python_renderer,
    nodejs_renderer
)

logger = logging.getLogger(__name__)


async def generate_test_cases(
    normalized_api: Any,
    cases_per_endpoint: int = 10,
    outputs: List[str] = None,
    domain_hint: str = None,
    seed: int = None,
    ai_speed: str = "fast"
) -> Dict[str, Any]:
    """
    Generate test cases and artifacts

    Args:
        normalized_api: Normalized API specification
        cases_per_endpoint: Number of cases per endpoint
        outputs: Output formats to generate
        domain_hint: Domain context hint
        seed: Random seed

    Returns:
        Dictionary of generated artifacts
    """
    if outputs is None:
        outputs = ["junit", "python", "nodejs", "postman"]

    artifacts = {
        "endpoint_count": len(normalized_api.endpoints),
        "cases_per_endpoint": cases_per_endpoint,
        "total_cases": 0
    }

    # Get AI provider based on speed preference
    provider = get_provider_for_speed(ai_speed)
    logger.info(f"Using provider: {provider.__class__.__name__} (speed: {ai_speed})")

    # Generate cases for each endpoint
    all_cases = []
    for endpoint in normalized_api.endpoints:
        options = {
            "count": cases_per_endpoint,
            "domain_hint": domain_hint,
            "seed": seed,
            "speed": ai_speed
        }

        cases = await provider.generate_cases(endpoint, options)

        # Validate and fix generated data
        for case in cases:
            if case.body and endpoint.request_body:
                if not validate_against_schema(case.body, endpoint.request_body):
                    case.body = fix_data_for_schema(case.body, endpoint.request_body)

        all_cases.extend(cases)

    artifacts["total_cases"] = len(all_cases)

    # Create multi-step flows
    flows = create_basic_flows(normalized_api.endpoints)

    # Generate requested outputs
    if "junit" in outputs:
        artifacts["junit"] = junit_restassured.render(
            all_cases,
            normalized_api,
            flows
        )

    if "postman" in outputs:
        artifacts["postman"] = postman.render(
            all_cases,
            normalized_api,
            flows
        )

    if "wiremock" in outputs:
        artifacts["wiremock"] = wiremock.render(
            all_cases,
            normalized_api
        )

    if "json" in outputs:
        artifacts["json"] = json_renderer.render(all_cases)

    if "python" in outputs:
        artifacts["python"] = python_renderer.render(
            all_cases,
            normalized_api,
            flows
        )

    if "nodejs" in outputs:
        artifacts["nodejs"] = nodejs_renderer.render(
            all_cases,
            normalized_api,
            flows
        )

    if "csv" in outputs:
        artifacts["csv"] = csv_renderer.render(all_cases)

    if "sql" in outputs:
        artifacts["sql"] = sql_renderer.render(
            all_cases,
            table_name=domain_hint or "test_data"
        )

    return artifacts
