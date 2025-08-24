"""Test case generation orchestration"""
import asyncio
import logging
from typing import Dict, Any, List
from app.ai.base import get_provider, get_provider_for_speed
from app.ai.null_provider import NullProvider
from app.utils.validation import validate_against_schema, fix_data_for_schema
from app.utils.flows import create_basic_flows
from app.utils.faker_utils import set_seed
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

# Global semaphore to limit concurrent AI requests
from app.config import settings
ai_semaphore = asyncio.Semaphore(settings.ai_concurrency_limit)

logger = logging.getLogger(__name__)


def create_test_data_json(cases):
    """Create test data JSON from generated cases"""
    test_data = []
    for case in cases:
        test_data.append({
            "endpoint": case.endpoint,
            "method": case.method,
            "body": case.body,
            "query_params": case.query_params,
            "path_params": case.path_params,
            "headers": case.headers
        })
    return test_data


def generate_junit_artifacts(cases, test_data):
    """Generate JUnit artifacts"""
    # Note: This function is deprecated and should not be used
    # The renderer expects (cases, api, flows) but we only have cases and test_data
    # For now, create a minimal API object with required fields
    from types import SimpleNamespace
    minimal_api = SimpleNamespace()
    minimal_api.title = "API"
    minimal_api.version = "1.0.0"
    minimal_api.description = "Generated API"
    
    return junit_restassured.render(cases, minimal_api, [])


def generate_python_artifacts(cases, test_data):
    """Generate Python artifacts"""
    return python_renderer.render(cases, test_data)


def generate_nodejs_artifacts(cases, test_data):
    """Generate Node.js artifacts"""
    return nodejs_renderer.render(cases, test_data)


def generate_postman_artifacts(cases, test_data):
    """Generate Postman artifacts"""
    return postman.render(cases, test_data)


def generate_csv_artifacts(cases):
    """Generate CSV artifacts"""
    return csv_renderer.render(cases)


def generate_sql_artifacts(cases):
    """Generate SQL artifacts"""
    return sql_renderer.render(cases)


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
    logger.info(f"generate_test_cases called with normalized_api type: {type(normalized_api)}")
    logger.info(f"normalized_api has endpoints: {hasattr(normalized_api, 'endpoints')}")
    if hasattr(normalized_api, 'endpoints'):
        logger.info(f"normalized_api.endpoints count: {len(normalized_api.endpoints)}")
    if hasattr(normalized_api, 'title'):
        logger.info(f"normalized_api.title: {normalized_api.title}")
    
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

    # Generate cases for each endpoint concurrently
    async def process_endpoint(endpoint):
        async with ai_semaphore:  # Limit concurrent AI requests
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

            return cases

    # Process all endpoints concurrently
    logger.info(f"Processing {len(normalized_api.endpoints)} endpoints concurrently")
    endpoint_tasks = [process_endpoint(endpoint) for endpoint in normalized_api.endpoints]
    endpoint_results = await asyncio.gather(*endpoint_tasks)
    
    # Flatten results
    all_cases = []
    for cases in endpoint_results:
        all_cases.extend(cases)
    
    # Clean up memory after processing
    del endpoint_results
    del endpoint_tasks
    import gc
    gc.collect()

    artifacts["total_cases"] = len(all_cases)

    # Create multi-step flows
    flows = create_basic_flows(normalized_api.endpoints)

    # Generate artifacts for each output format
    if "junit" in outputs:
        logger.info(f"Calling junit_restassured.render with all_cases type: {type(all_cases)}, normalized_api type: {type(normalized_api)}, flows type: {type(flows)}")
        logger.info(f"normalized_api has title: {hasattr(normalized_api, 'title')}")
        if hasattr(normalized_api, 'title'):
            logger.info(f"normalized_api.title: {normalized_api.title}")
        artifacts["junit"] = junit_restassured.render(all_cases, normalized_api, flows)

    if "postman" in outputs:
        artifacts["postman"] = postman.render(all_cases, normalized_api, flows)

    if "wiremock" in outputs:
        artifacts["wiremock"] = wiremock.render(all_cases, normalized_api, flows)

    if "python" in outputs:
        artifacts["python"] = python_renderer.render(all_cases, normalized_api, flows)

    if "nodejs" in outputs:
        artifacts["nodejs"] = nodejs_renderer.render(all_cases, normalized_api, flows)

    if "json" in outputs:
        artifacts["json"] = flows

    if "csv" in outputs:
        artifacts["csv"] = csv_renderer.render(all_cases)

    if "sql" in outputs:
        artifacts["sql"] = sql_renderer.render(
            all_cases,
            table_name=domain_hint or "test_data"
        )

    return artifacts

async def generate_test_cases_with_progress(
    task_id: str,
    normalized_spec: Any,
    cases_per_endpoint: int = 10,
    outputs: List[str] = None,
    domain_hint: str = None,
    seed: int = None,
    ai_speed: str = "fast"
) -> Dict[str, Any]:
    """Generate test cases with real-time progress updates"""
    from app.main import update_progress
    
    if outputs is None:
        outputs = ["junit", "python", "nodejs", "postman"]
    
    if seed is not None:
        set_seed(seed)
    
    # Get AI provider based on speed preference
    provider = get_provider_for_speed(ai_speed)
    
    if not provider.is_available():
        logger.warning(f"AI provider for speed '{ai_speed}' not available, falling back to null provider")
        provider = NullProvider()
    
    logger.info(f"Using provider: {provider.__class__.__name__} (speed: {ai_speed})")
    
    # Process endpoints with progress updates
    total_endpoints = len(normalized_spec.endpoints)
    await update_progress(task_id, "generating", 30, f"Processing {total_endpoints} endpoints...")
    
    endpoint_results = []
    for i, endpoint in enumerate(normalized_spec.endpoints):
        # Update progress for each endpoint
        progress = 30 + int((i / total_endpoints) * 60)  # 30% to 90%
        await update_progress(
            task_id, 
            "generating", 
            progress, 
            f"Generating test cases for endpoint {i+1}/{total_endpoints}: {endpoint.method} {endpoint.path}",
            total_endpoints,
            i + 1
        )
        
        # Generate cases for this endpoint
        cases = await provider.generate_cases(endpoint, {
            "count": cases_per_endpoint,
            "domain_hint": domain_hint,
            "speed": ai_speed
        })
        
        endpoint_results.append(cases)
    
    # Flatten results
    all_cases = []
    for cases in endpoint_results:
        all_cases.extend(cases)
    
    # Clean up memory after processing
    del endpoint_results
    import gc
    gc.collect()
    
    # Create test data JSON
    test_data = create_test_data_json(all_cases)
    
    # Generate artifacts for each output format
    artifacts = {}
    
    for output_format in outputs:
        if output_format == "junit":
            artifacts["junit"] = generate_junit_artifacts(all_cases, test_data)
        elif output_format == "python":
            artifacts["python"] = generate_python_artifacts(all_cases, test_data)
        elif output_format == "nodejs":
            artifacts["nodejs"] = generate_nodejs_artifacts(all_cases, test_data)
        elif output_format == "postman":
            artifacts["postman"] = generate_postman_artifacts(all_cases, test_data)
        elif output_format == "csv":
            artifacts["csv"] = generate_csv_artifacts(all_cases)
        elif output_format == "sql":
            artifacts["sql"] = generate_sql_artifacts(all_cases)
        elif output_format == "json":
            artifacts["json"] = test_data
    
    await update_progress(task_id, "generating", 90, "Test cases generated, creating artifacts...")
    
    return artifacts
