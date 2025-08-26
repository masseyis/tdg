#!/usr/bin/env python3
"""
CI Monitor Script

This script monitors GitHub Actions CI runs and provides detailed feedback on failures.
It can be run manually or as part of a monitoring system.

Usage:
    python scripts/ci_monitor.py [--wait] [--timeout 300] [--run-id RUN_ID]
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def run_gh_command(args: list) -> Dict[str, Any]:
    """Run a GitHub CLI command and return the JSON result"""
    try:
        result = subprocess.run(
            ['gh'] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ GitHub CLI command failed: {' '.join(args)}")
        print(f"Error: {e.stderr}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return {}


def get_latest_run() -> Optional[Dict[str, Any]]:
    """Get the latest GitHub Actions run"""
    runs = run_gh_command(['run', 'list', '--limit', '1', '--json', 'status,conclusion,url,createdAt,displayTitle,number'])
    if isinstance(runs, list) and runs:
        return runs[0]
    return None


def get_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific run"""
    return run_gh_command(['run', 'view', run_id, '--json', 'status,conclusion,url,createdAt,displayTitle,number,workflowName'])


def get_run_logs(run_id: str) -> str:
    """Get the logs for a specific run"""
    try:
        result = subprocess.run(
            ['gh', 'run', 'view', run_id, '--log'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Failed to get logs: {e.stderr}"


def analyze_failure(logs: str) -> Dict[str, Any]:
    """Analyze failure logs and extract key information"""
    analysis = {
        'error_type': 'unknown',
        'error_message': '',
        'suggested_fix': '',
        'test_failures': [],
        'compilation_errors': [],
        'timeout_issues': []
    }
    
    lines = logs.split('\n')
    
    # Look for common failure patterns
    for line in lines:
        line_lower = line.lower()
        
        # Test failures
        if 'failed' in line_lower and 'test' in line_lower:
            analysis['test_failures'].append(line.strip())
        
        # Compilation errors
        if 'compilation failure' in line_lower or 'cannot find symbol' in line_lower:
            analysis['compilation_errors'].append(line.strip())
        
        # Timeout issues
        if 'timeout' in line_lower or 'timed out' in line_lower:
            analysis['timeout_issues'].append(line.strip())
        
        # E2E test specific failures
        if 'e2e' in line_lower and 'failed' in line_lower:
            analysis['error_type'] = 'e2e_test_failure'
            analysis['error_message'] = line.strip()
        
        # Node.js specific failures
        if 'npm' in line_lower and 'install' in line_lower and 'failed' in line_lower:
            analysis['error_type'] = 'nodejs_dependency_failure'
            analysis['error_message'] = line.strip()
            analysis['suggested_fix'] = 'Check Node.js dependencies and package.json configuration'
        
        # Download failures
        if 'download' in line_lower and 'failed' in line_lower:
            analysis['error_type'] = 'download_failure'
            analysis['error_message'] = line.strip()
            analysis['suggested_fix'] = 'Check browser download configuration and file paths'
    
    return analysis


def print_run_status(run: Dict[str, Any], detailed: bool = False):
    """Print formatted run status"""
    status_emoji = {
        'completed': '✅' if run.get('conclusion') == 'success' else '❌',
        'in_progress': '🔄',
        'queued': '⏳',
        'waiting': '⏳'
    }
    
    status = run.get('status', 'unknown')
    emoji = status_emoji.get(status, '❓')
    
    print(f"\n{emoji} Run #{run.get('number', 'N/A')}: {run.get('displayTitle', 'Unknown')}")
    print(f"   Status: {status}")
    print(f"   Conclusion: {run.get('conclusion', 'N/A')}")
    print(f"   Created: {run.get('createdAt', 'N/A')}")
    print(f"   URL: {run.get('url', 'N/A')}")
    
    if detailed and run.get('conclusion') == 'failure':
        print(f"\n🔍 Analyzing failure...")
        logs = get_run_logs(str(run.get('number', '')))
        analysis = analyze_failure(logs)
        
        if analysis['error_type'] != 'unknown':
            print(f"   Error Type: {analysis['error_type']}")
            print(f"   Error Message: {analysis['error_message']}")
            if analysis['suggested_fix']:
                print(f"   Suggested Fix: {analysis['suggested_fix']}")
        
        if analysis['test_failures']:
            print(f"\n   Test Failures ({len(analysis['test_failures'])}):")
            for failure in analysis['test_failures'][:5]:  # Show first 5
                print(f"     - {failure}")
        
        if analysis['compilation_errors']:
            print(f"\n   Compilation Errors ({len(analysis['compilation_errors'])}):")
            for error in analysis['compilation_errors'][:3]:  # Show first 3
                print(f"     - {error}")


def monitor_ci(wait: bool = False, timeout: int = 300, run_id: Optional[str] = None):
    """Monitor CI runs"""
    print("🔍 CI Monitor Starting...")
    print(f"   Wait: {wait}")
    print(f"   Timeout: {timeout}s")
    if run_id:
        print(f"   Run ID: {run_id}")
    
    start_time = time.time()
    
    while True:
        if run_id:
            run = get_run_details(run_id)
        else:
            run = get_latest_run()
        
        if not run:
            print("❌ No run found")
            break
        
        print_run_status(run, detailed=True)
        
        # Check if we should continue monitoring
        if not wait:
            break
        
        status = run.get('status', 'unknown')
        if status in ['completed', 'cancelled']:
            print(f"\n✅ Run completed with status: {status}")
            break
        
        # Check timeout
        if time.time() - start_time > timeout:
            print(f"\n⏰ Timeout reached ({timeout}s)")
            break
        
        print(f"\n⏳ Waiting 30s before next check...")
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description='Monitor GitHub Actions CI runs')
    parser.add_argument('--wait', action='store_true', help='Wait for run to complete')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds (default: 300)')
    parser.add_argument('--run-id', type=str, help='Specific run ID to monitor')
    
    args = parser.parse_args()
    
    try:
        monitor_ci(wait=args.wait, timeout=args.timeout, run_id=args.run_id)
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
