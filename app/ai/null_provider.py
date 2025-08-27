"""Null AI provider - uses faker and heuristics only"""

import random
from typing import Any, Dict, List, Optional

from app.ai.base import AIProvider, TestCase
from app.progress import ProgressCallback
from app.ai.prompts import order_test_cases
from app.utils.faker_utils import (
    generate_boundary_value,
    generate_for_schema,
    generate_negative_value,
    set_seed,
)


class NullProvider(AIProvider):
    """Null provider using faker and heuristics"""

    def is_available(self) -> bool:
        """Always available"""
        return True

    async def generate_cases(
        self,
        endpoint: Any,
        options: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[TestCase]:
        """Generate test cases using faker and heuristics"""
        cases = []
        count = options.get("count", 10)
        domain_hint = options.get("domain_hint")
        seed = options.get("seed")

        if seed:
            set_seed(seed)

        # Calculate distribution - for POST operations, prioritize valid cases with rich data
        if endpoint.method == "POST":
            valid_count = max(count * 2 // 3, count // 2)  # More valid cases for POST
            boundary_count = max(1, count // 4)
            negative_count = max(1, count - valid_count - boundary_count)
        else:
            valid_count = max(1, count // 2)
            boundary_count = max(1, count // 3)
            negative_count = max(1, count - valid_count - boundary_count)

        # Generate valid cases
        for i in range(valid_count):
            case = self._generate_valid_case(endpoint, domain_hint, i)
            cases.append(case)

        # Generate boundary cases
        for i in range(boundary_count):
            case = self._generate_boundary_case(endpoint, domain_hint, i)
            cases.append(case)

        # Generate negative cases
        for i in range(negative_count):
            case = self._generate_negative_case(endpoint, domain_hint, i)
            cases.append(case)

        # Order test cases logically: CREATE → READ → UPDATE → DELETE
        ordered_cases = order_test_cases(cases)

        return ordered_cases

    def _generate_valid_case(self, endpoint: Any, domain_hint: str, index: int) -> TestCase:
        """Generate a valid test case"""
        # Generate path params
        path_params = {}
        for param in endpoint.parameters:
            if param.location == "path":
                path_params[param.name] = self._generate_param_value(param, domain_hint)

        # Generate query params
        query_params = {}
        for param in endpoint.parameters:
            if param.location == "query" and (param.required or random.random() > 0.5):
                query_params[param.name] = self._generate_param_value(param, domain_hint)

        # Generate headers
        headers = {"Content-Type": "application/json"}
        for param in endpoint.parameters:
            if param.location == "header" and (param.required or random.random() > 0.5):
                headers[param.name] = str(self._generate_param_value(param, domain_hint))

        # Generate body
        body = None
        if endpoint.request_body:
            body = generate_for_schema(endpoint.request_body, domain_hint)

        return TestCase(
            name=f"Valid_{endpoint.operation_id or endpoint.method}_{index}",
            description=f"Valid test case for {endpoint.method} {endpoint.path}",
            method=endpoint.method,
            path=endpoint.path,
            headers=headers,
            query_params=query_params,
            path_params=path_params,
            body=body,
            expected_status=(
                200 if endpoint.method == "GET" else 201 if endpoint.method == "POST" else 200
            ),
            expected_response=None,
            test_type="valid",
        )

    def _generate_boundary_case(self, endpoint: Any, domain_hint: str, index: int) -> TestCase:
        """Generate a boundary test case"""
        base_case = self._generate_valid_case(endpoint, domain_hint, index)
        base_case.name = f"Boundary_{endpoint.operation_id or endpoint.method}_{index}"
        base_case.description = f"Boundary test case for {endpoint.method} {endpoint.path}"
        base_case.test_type = "boundary"

        # Modify body with boundary values
        if endpoint.request_body and base_case.body:
            base_case.body = generate_boundary_value(endpoint.request_body)

        return base_case

    def _generate_negative_case(self, endpoint: Any, domain_hint: str, index: int) -> TestCase:
        """Generate a negative test case"""
        base_case = self._generate_valid_case(endpoint, domain_hint, index)
        base_case.name = f"Negative_{endpoint.operation_id or endpoint.method}_{index}"
        base_case.description = f"Negative test case for {endpoint.method} {endpoint.path}"
        base_case.test_type = "negative"

        # Choose negative scenario
        scenario = random.choice(["missing_required", "invalid_type", "auth_failure"])

        if scenario == "missing_required" and endpoint.request_body:
            # Remove required field
            if base_case.body and isinstance(base_case.body, dict):
                required = endpoint.request_body.get("required", [])
                if required:
                    base_case.body.pop(required[0], None)
            base_case.expected_status = 400

        elif scenario == "invalid_type" and endpoint.request_body:
            # Use invalid data
            base_case.body = generate_negative_value(endpoint.request_body)
            base_case.expected_status = 400

        elif scenario == "auth_failure":
            # Remove auth header
            base_case.headers.pop("Authorization", None)
            base_case.expected_status = 401

        return base_case

    def _generate_param_value(self, param: Any, domain_hint: str) -> Any:
        """Generate value for a parameter"""
        if param.schema:
            return generate_for_schema(param.schema, domain_hint)

        # Default based on common param names
        name_lower = param.name.lower()
        if "id" in name_lower:
            return random.randint(1, 1000)
        elif "page" in name_lower or "limit" in name_lower:
            return random.randint(1, 100)
        elif "sort" in name_lower:
            return random.choice(["asc", "desc"])
        else:
            return f"test_{param.name}"  # Test Data Generator MVP Repository
