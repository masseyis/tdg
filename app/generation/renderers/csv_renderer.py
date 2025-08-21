"""CSV renderer for test data"""
import csv
import io
from typing import List, Any


def render(cases: List[Any]) -> str:
    """
    Render test cases as CSV
    
    Returns:
        CSV string
    """
    output = io.StringIO()
    
    # Collect all unique fields
    all_fields = set()
    for case in cases:
        all_fields.add("name")
        all_fields.add("method")
        all_fields.add("path")
        all_fields.add("expected_status")
        all_fields.add("test_type")
        
        if case.body:
            for key in case.body.keys():
                all_fields.add(f"body.{key}")
        
        for key in case.query_params.keys():
            all_fields.add(f"query.{key}")
        
        for key in case.path_params.keys():
            all_fields.add(f"path.{key}")
    
    # Ensure core fields come first
    core_fields = ["name", "method", "path", "expected_status", "test_type"]
    other_fields = sorted([f for f in all_fields if f not in core_fields])
    fieldnames = core_fields + other_fields
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write rows
    for case in cases:
        row = {
            "name": case.name,
            "method": case.method,
            "path": case.path,
            "expected_status": case.expected_status,
            "test_type": case.test_type
        }
        
        # Add body fields
        if case.body:
            for key, value in case.body.items():
                row[f"body.{key}"] = value
        
        # Add query params
        for key, value in case.query_params.items():
            row[f"query.{key}"] = value
        
        # Add path params
        for key, value in case.path_params.items():
            row[f"path.{key}"] = value
        
        writer.writerow(row)
    
    return output.getvalue()