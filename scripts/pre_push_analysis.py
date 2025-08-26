#!/usr/bin/env python3
"""
Pre-Push Analysis Script

This script performs git diff analysis and documents architectural changes
before pushing code to the repository.

Usage:
    python scripts/pre_push_analysis.py
"""

import os
import sys
import subprocess
import re
from datetime import datetime
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_git_diff():
    """Get the git diff for the current changes."""
    success, stdout, stderr = run_command("git diff --cached")
    if not success:
        print(f"❌ Failed to get git diff: {stderr}")
        return None
    return stdout

def get_git_status():
    """Get the git status for current changes."""
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        print(f"❌ Failed to get git status: {stderr}")
        return None
    return stdout

def analyze_changes(diff_output, status_output):
    """Analyze the changes to identify architectural modifications."""
    changes = {
        'new_files': [],
        'modified_files': [],
        'deleted_files': [],
        'architectural_changes': [],
        'test_changes': [],
        'documentation_changes': [],
        'configuration_changes': []
    }
    
    if not diff_output and not status_output:
        return changes
    
    # Parse git status
    if status_output:
        for line in status_output.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]
            
            if status.startswith('A'):  # Added
                changes['new_files'].append(filename)
            elif status.startswith('M'):  # Modified
                changes['modified_files'].append(filename)
            elif status.startswith('D'):  # Deleted
                changes['deleted_files'].append(filename)
    
    # Analyze file types and patterns
    all_files = changes['new_files'] + changes['modified_files']
    
    for filename in all_files:
        if filename.endswith('.py'):
            if 'test_' in filename or 'tests/' in filename:
                changes['test_changes'].append(filename)
            elif any(pattern in filename for pattern in ['main.py', 'app/', 'models/', 'services/']):
                changes['architectural_changes'].append(filename)
        elif filename.endswith(('.md', '.txt', '.rst')):
            changes['documentation_changes'].append(filename)
        elif filename.endswith(('.yml', '.yaml', '.json', '.toml', '.ini', '.cfg')):
            changes['configuration_changes'].append(filename)
        elif filename.endswith(('.html', '.js', '.css', '.ts', '.tsx')):
            changes['architectural_changes'].append(filename)
        elif filename.endswith(('.sql', '.db', '.sqlite')):
            changes['architectural_changes'].append(filename)
    
    return changes

def identify_architectural_patterns(diff_output):
    """Identify specific architectural patterns in the diff."""
    patterns = {
        'new_endpoints': [],
        'database_changes': [],
        'api_changes': [],
        'frontend_changes': [],
        'test_additions': [],
        'configuration_changes': []
    }
    
    if not diff_output:
        return patterns
    
    lines = diff_output.split('\n')
    
    for line in lines:
        # Look for new API endpoints
        if '+@app.' in line and any(method in line for method in ['.get(', '.post(', '.put(', '.delete(']):
            patterns['new_endpoints'].append(line.strip())
        
        # Look for database/schema changes
        if any(keyword in line.lower() for keyword in ['create table', 'alter table', 'drop table', 'migration']):
            patterns['database_changes'].append(line.strip())
        
        # Look for API changes
        if any(keyword in line for keyword in ['class', 'def ', 'async def', 'import ', 'from ']):
            if 'app/' in line or 'models/' in line or 'services/' in line:
                patterns['api_changes'].append(line.strip())
        
        # Look for frontend changes
        if any(keyword in line for keyword in ['function', 'const ', 'let ', 'var ', 'document.', 'window.']):
            if any(ext in line for ext in ['.html', '.js', '.css', '.ts']):
                patterns['frontend_changes'].append(line.strip())
        
        # Look for test additions
        if 'def test_' in line or 'class Test' in line:
            patterns['test_additions'].append(line.strip())
        
        # Look for configuration changes
        if any(keyword in line for keyword in ['DEBUG', 'SECRET', 'DATABASE', 'API_KEY', 'ENVIRONMENT']):
            patterns['configuration_changes'].append(line.strip())
    
    return patterns

def generate_architectural_summary(changes, patterns):
    """Generate a summary of architectural changes."""
    summary = []
    
    if changes['architectural_changes']:
        summary.append("🏗️ **Architectural Changes Detected:**")
        for file in changes['architectural_changes']:
            summary.append(f"  - {file}")
        summary.append("")
    
    if patterns['new_endpoints']:
        summary.append("🔌 **New API Endpoints:**")
        for endpoint in patterns['new_endpoints'][:5]:  # Limit to first 5
            summary.append(f"  - {endpoint}")
        if len(patterns['new_endpoints']) > 5:
            summary.append(f"  - ... and {len(patterns['new_endpoints']) - 5} more")
        summary.append("")
    
    if patterns['database_changes']:
        summary.append("🗄️ **Database Changes:**")
        for change in patterns['database_changes'][:3]:  # Limit to first 3
            summary.append(f"  - {change}")
        if len(patterns['database_changes']) > 3:
            summary.append(f"  - ... and {len(patterns['database_changes']) - 3} more")
        summary.append("")
    
    if changes['test_changes']:
        summary.append("🧪 **Test Changes:**")
        for file in changes['test_changes']:
            summary.append(f"  - {file}")
        summary.append("")
    
    if changes['new_files']:
        summary.append("📁 **New Files:**")
        for file in changes['new_files']:
            summary.append(f"  - {file}")
        summary.append("")
    
    return "\n".join(summary)

def update_architectural_changes_file(summary, changes, patterns):
    """Update the ARCHITECTURAL_CHANGES.md file with new entry."""
    changes_file = Path("ARCHITECTURAL_CHANGES.md")
    
    if not changes_file.exists():
        print("❌ ARCHITECTURAL_CHANGES.md not found")
        return False
    
    # Read current content
    with open(changes_file, 'r') as f:
        content = f.read()
    
    # Generate new entry
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Determine change type
    change_type = "General"
    if patterns['new_endpoints']:
        change_type = "API"
    elif patterns['database_changes']:
        change_type = "Database"
    elif any('frontend' in file.lower() for file in changes['architectural_changes']):
        change_type = "Frontend"
    elif patterns['configuration_changes']:
        change_type = "Infrastructure"
    
    # Generate entry
    entry = f"""
### {today} - [Auto-detected Change]

**Change Type**: {change_type}

**Summary**: {len(changes['architectural_changes'])} architectural files modified, {len(changes['new_files'])} new files added

**Rationale**: [To be filled manually]

**Implementation**: [To be filled manually]

**Pros**:
- ✅ [To be filled manually]

**Cons**:
- ⚠️ [To be filled manually]

**Impact**: [To be filled manually]

**Migration**: [To be filled manually]

**Auto-detected Changes**:
{summary}

---
"""
    
    # Insert after the "Recent Changes" section
    if "## Recent Changes" in content:
        parts = content.split("## Recent Changes")
        new_content = parts[0] + "## Recent Changes" + entry + parts[1]
    else:
        new_content = content + entry
    
    # Write back
    with open(changes_file, 'w') as f:
        f.write(new_content)
    
    return True

def run_tests():
    """Run the test suite to ensure changes work."""
    print("🧪 Running test suite...")
    
    # Run unit tests
    success, stdout, stderr = run_command("python -m pytest tests/ -v --tb=short")
    if not success:
        print("❌ Unit tests failed!")
        print(stderr)
        return False
    
    # Run E2E tests
    print("🔍 Running E2E tests...")
    success, stdout, stderr = run_command("python -m pytest tests/test_e2e_functional.py::test_complete_user_experience -v")
    if not success:
        print("❌ E2E tests failed!")
        print(stderr)
        return False
    
    print("✅ All tests passed!")
    return True

def main():
    """Main function to perform pre-push analysis."""
    print("🔍 Performing pre-push analysis...")
    print("=" * 50)
    
    # Get git diff and status
    diff_output = get_git_diff()
    status_output = get_git_status()
    
    if not diff_output and not status_output:
        print("ℹ️  No changes detected")
        return True
    
    # Analyze changes
    changes = analyze_changes(diff_output, status_output)
    patterns = identify_architectural_patterns(diff_output)
    
    # Generate summary
    summary = generate_architectural_summary(changes, patterns)
    
    if summary:
        print("📋 Change Summary:")
        print(summary)
        print("=" * 50)
        
        # Update architectural changes file
        if changes['architectural_changes'] or changes['new_files']:
            print("📝 Updating ARCHITECTURAL_CHANGES.md...")
            if update_architectural_changes_file(summary, changes, patterns):
                print("✅ Architectural changes documented")
            else:
                print("❌ Failed to update architectural changes file")
    
    # Run tests
    print("🧪 Validating changes with tests...")
    if not run_tests():
        print("❌ Tests failed - please fix before pushing")
        return False
    
    print("✅ Pre-push analysis complete!")
    print("📝 Remember to:")
    print("  - Review the architectural changes entry")
    print("  - Fill in the rationale, pros, and cons")
    print("  - Update any related documentation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
