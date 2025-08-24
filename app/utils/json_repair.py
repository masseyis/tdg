"""
JSON repair utility for fixing malformed JSON from AI models

This module provides functions to automatically repair common JSON syntax errors
that occur when AI models generate JSON responses.
"""

import json
import re
import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)


class JSONRepairError(Exception):
    """Exception raised when JSON repair fails"""
    pass


def repair_json(content: str) -> str:
    """
    Attempt to repair malformed JSON content
    
    Args:
        content: The potentially malformed JSON string
        
    Returns:
        Repaired JSON string
        
    Raises:
        JSONRepairError: If repair fails
    """
    if not content or not content.strip():
        raise JSONRepairError("Empty or invalid content")
    
    # Try to parse as-is first
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        logger.info("JSON parsing failed, attempting repair...")
    
    # Apply various repair strategies
    repaired = content
    
    # Strategy 1: Fix common quote issues
    repaired = _fix_quote_issues(repaired)
    
    # Strategy 2: Fix missing commas
    repaired = _fix_missing_commas(repaired)
    
    # Strategy 3: Fix unterminated strings
    repaired = _fix_unterminated_strings(repaired)
    
    # Strategy 4: Fix truncated content
    repaired = _fix_truncated_content(repaired)
    
    # Strategy 5: Fix malformed property names
    repaired = _fix_property_names(repaired)
    
    # Strategy 6: Fix array/object termination
    repaired = _fix_termination(repaired)
    
    # Try to parse the repaired JSON
    try:
        json.loads(repaired)
        logger.info("JSON repair successful")
        return repaired
    except json.JSONDecodeError as e:
        logger.warning(f"JSON repair failed: {e}")
        # Try one more aggressive repair
        final_attempt = _aggressive_repair(repaired)
        try:
            json.loads(final_attempt)
            logger.info("Aggressive JSON repair successful")
            return final_attempt
        except json.JSONDecodeError:
            raise JSONRepairError(f"Failed to repair JSON after all attempts: {e}")


def _fix_quote_issues(content: str) -> str:
    """Fix common quote-related issues"""
    # Fix unescaped quotes in strings
    # Look for patterns like: "description": "This has "quotes" inside"
    content = re.sub(r'("description":\s*"[^"]*)"([^"]*)"([^"]*")', r'\1\\"\2\\"\3', content)
    
    # Fix missing quotes around property names
    content = re.sub(r'(\s+)(\w+)(\s*:)', r'\1"\2"\3', content)
    
    # Fix missing quotes around string values
    content = re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', content)
    
    return content


def _fix_missing_commas(content: str) -> str:
    """Fix missing commas between array elements and object properties"""
    # Add missing commas between array elements
    content = re.sub(r'(\})\s*(\{)', r'\1,\2', content)
    
    # Add missing commas between object properties
    content = re.sub(r'(")\s*(\{)', r'\1,\2', content)
    
    # Add missing commas after array elements
    content = re.sub(r'(\])\s*(")', r'\1,\2', content)
    
    # Add missing commas after object properties
    content = re.sub(r'(")\s*(")', r'\1,\2', content)
    
    return content


def _fix_unterminated_strings(content: str) -> str:
    """Fix unterminated string literals"""
    # Find strings that don't end with a quote
    # Look for patterns like: "description": "This is incomplete
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Check if line has an unclosed string
        if '"' in line and line.count('"') % 2 == 1:
            # Find the last quote and add a closing quote
            last_quote_pos = line.rfind('"')
            if last_quote_pos > 0:
                # Check if this is a property value
                if ':' in line[:last_quote_pos]:
                    # Add closing quote and comma if needed
                    if not line.rstrip().endswith(','):
                        line = line.rstrip() + '",'
                    else:
                        line = line.rstrip() + '"'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def _fix_truncated_content(content: str) -> str:
    """Fix truncated JSON content by completing incomplete structures"""
    # Count braces and brackets to see what's incomplete
    open_braces = content.count('{') - content.count('}')
    open_brackets = content.count('[') - content.count(']')
    
    # Complete the content
    if open_braces > 0:
        content += '}' * open_braces
    
    if open_brackets > 0:
        content += ']' * open_brackets
    
    # If content ends with a comma, remove it
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    return content


def _fix_property_names(content: str) -> str:
    """Fix malformed property names"""
    # Fix property names without quotes
    content = re.sub(r'(\s+)(\w+)(\s*:)', r'\1"\2"\3', content)
    
    # Fix property names with single quotes
    content = re.sub(r"'(\w+)':", r'"\1":', content)
    
    return content


def _fix_termination(content: str) -> str:
    """Fix incomplete array and object termination"""
    # Find the last complete structure
    last_complete = _find_last_complete_structure(content)
    
    if last_complete:
        # Remove everything after the last complete structure
        content = content[:last_complete]
    
    return content


def _find_last_complete_structure(content: str) -> Optional[int]:
    """Find the position of the last complete JSON structure"""
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(content):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        elif char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        
        # If we've closed all structures, this is a complete point
        if brace_count == 0 and bracket_count == 0:
            return i + 1
    
    return None


def _aggressive_repair(content: str) -> str:
    """Apply aggressive repair strategies when normal repair fails"""
    # Try to extract just the cases array if it exists
    cases_match = re.search(r'(\{\s*"cases"\s*:\s*\[.*?\])', content, re.DOTALL)
    if cases_match:
        extracted = cases_match.group(1)
        # Try to complete it
        if not extracted.rstrip().endswith('}'):
            extracted += '}'
        return extracted
    
    # If no cases array, try to create a minimal valid structure
    if '"cases"' in content:
        # Find the start of cases array
        start = content.find('"cases"')
        if start > 0:
            # Extract from cases onwards and complete
            partial = content[start-1:]  # Include the opening brace
            if not partial.rstrip().endswith('}'):
                partial += '}'
            return '{' + partial
    
    # Last resort: create a minimal valid structure
    return '{"cases": []}'


def extract_json_from_content(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract and repair JSON from content that might contain extra text
    
    Args:
        content: Content that might contain JSON
        
    Returns:
        Parsed JSON object or None if extraction fails
    """
    # Look for JSON content between curly braces
    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
    if not json_match:
        return None
    
    json_content = json_match.group(1)
    
    try:
        # Try to repair and parse
        repaired = repair_json(json_content)
        return json.loads(repaired)
    except JSONRepairError:
        logger.warning("Failed to extract valid JSON from content")
        return None


def validate_and_repair_json(content: str) -> Optional[Dict[str, Any]]:
    """
    Validate JSON and attempt repair if needed
    
    Args:
        content: JSON content to validate
        
    Returns:
        Valid JSON object or None if all repair attempts fail
    """
    try:
        # First try to parse as-is
        return json.loads(content)
    except json.JSONDecodeError:
        logger.info("Initial JSON parsing failed, attempting repair...")
        
        try:
            # Try to repair
            repaired = repair_json(content)
            return json.loads(repaired)
        except JSONRepairError:
            logger.warning("JSON repair failed")
            return None


# Convenience function for common use case
def safe_json_parse(content: str, default: Any = None) -> Any:
    """
    Safely parse JSON with automatic repair
    
    Args:
        content: JSON content to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed JSON object or default value
    """
    try:
        return validate_and_repair_json(content)
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return default
