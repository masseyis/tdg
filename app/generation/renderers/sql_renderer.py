"""SQL renderer for test data"""
from typing import List, Any
import json


def render(cases: List[Any], table_name: str = "test_data") -> str:
    """
    Render test cases as SQL INSERT statements
    
    Returns:
        SQL string
    """
    sql_lines = []
    
    # Create table
    sql_lines.append(f"-- Test data for {table_name}")
    sql_lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
    sql_lines.append("    id SERIAL PRIMARY KEY,")
    sql_lines.append("    test_name VARCHAR(255),")
    sql_lines.append("    method VARCHAR(10),")
    sql_lines.append("    path VARCHAR(500),")
    sql_lines.append("    body JSONB,")
    sql_lines.append("    query_params JSONB,")
    sql_lines.append("    path_params JSONB,")
    sql_lines.append("    expected_status INTEGER,")
    sql_lines.append("    test_type VARCHAR(50),")
    sql_lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    sql_lines.append(");")
    sql_lines.append("")
    
    # Insert statements
    sql_lines.append(f"-- Insert test cases")
    for case in cases:
        # Convert case data to SQL
        test_name = case.name.replace("'", "''") if case.name else "Unknown"
        method = case.method
        path = case.path.replace("'", "''") if case.path else ""
        body = json.dumps(case.body) if case.body else "null"
        query_params = json.dumps(case.query_params) if case.query_params else "null"
        path_params = json.dumps(case.path_params) if case.path_params else "null"
        expected_status = case.expected_status or 200
        test_type = case.test_type or "valid"
        
        sql_lines.append(
            f"INSERT INTO {table_name} (test_name, method, path, body, query_params, path_params, expected_status, test_type) "
            f"VALUES ('{test_name}', '{method}', '{path}', '{body}', '{query_params}', '{path_params}', {expected_status}, '{test_type}');"
        )