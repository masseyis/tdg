#!/usr/bin/env python3
"""
Post-Push CI Monitor

This script is designed to be run after a git push to automatically monitor CI results.
It waits for the CI to start and then monitors the results.

Usage:
    python scripts/post_push_monitor.py [--timeout 600] [--notify]
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

# Import the CI monitor functions
from ci_monitor import monitor_ci, get_latest_run


def wait_for_new_run(initial_run_id: Optional[str] = None, timeout: int = 120) -> Optional[str]:
    """Wait for a new CI run to start after push"""
    print(f"⏳ Waiting for new CI run to start (timeout: {timeout}s)...")
    
    start_time = time.time()
    last_run_id = initial_run_id
    
    while time.time() - start_time < timeout:
        run = get_latest_run()
        if run:
            current_run_id = str(run.get('number', ''))
            
            # If this is a new run (different from the last one we saw)
            if current_run_id != last_run_id:
                print(f"✅ New CI run detected: #{current_run_id}")
                return current_run_id
            
            # If the run is in progress and we haven't seen it before
            status = run.get('status', 'unknown')
            if status == 'in_progress' and not last_run_id:
                print(f"✅ CI run in progress: #{current_run_id}")
                return current_run_id
        
        time.sleep(10)
    
    print(f"⏰ Timeout waiting for new CI run")
    return None


def notify_failure(run_id: str, error_type: str, error_message: str):
    """Send notification about CI failure"""
    print(f"\n🚨 CI FAILURE ALERT 🚨")
    print(f"   Run ID: {run_id}")
    print(f"   Error Type: {error_type}")
    print(f"   Error Message: {error_message}")
    print(f"   URL: https://github.com/masseyis/tdg/actions/runs/{run_id}")
    
    # You can add more notification methods here:
    # - Slack webhook
    # - Email
    # - SMS
    # - Desktop notification


def main():
    parser = argparse.ArgumentParser(description='Monitor CI after git push')
    parser.add_argument('--timeout', type=int, default=600, help='Total timeout in seconds (default: 600)')
    parser.add_argument('--notify', action='store_true', help='Send notifications on failure')
    parser.add_argument('--wait-for-start', type=int, default=120, help='Wait time for CI to start (default: 120)')
    
    args = parser.parse_args()
    
    print("🚀 Post-Push CI Monitor Starting...")
    print(f"   Total Timeout: {args.timeout}s")
    print(f"   Wait for Start: {args.wait_for_start}s")
    print(f"   Notifications: {args.notify}")
    
    # Get the current latest run before we start
    initial_run = get_latest_run()
    initial_run_id = str(initial_run.get('number', '')) if initial_run else None
    
    if initial_run_id:
        print(f"   Current latest run: #{initial_run_id}")
    
    # Wait for a new run to start
    new_run_id = wait_for_new_run(initial_run_id, args.wait_for_start)
    
    if not new_run_id:
        print("❌ No new CI run detected")
        sys.exit(1)
    
    # Monitor the new run
    print(f"\n🔍 Monitoring CI run #{new_run_id}...")
    
    # Calculate remaining timeout
    elapsed = time.time() - (time.time() - args.wait_for_start)
    remaining_timeout = max(60, args.timeout - elapsed)
    
    try:
        monitor_ci(wait=True, timeout=int(remaining_timeout), run_id=new_run_id)
        
        # Check final status
        run = get_latest_run()
        if run and str(run.get('number', '')) == new_run_id:
            conclusion = run.get('conclusion', 'unknown')
            
            if conclusion == 'success':
                print(f"\n🎉 CI run #{new_run_id} completed successfully!")
                sys.exit(0)
            elif conclusion == 'failure':
                print(f"\n❌ CI run #{new_run_id} failed!")
                
                if args.notify:
                    # Get failure details for notification
                    from ci_monitor import get_run_logs, analyze_failure
                    logs = get_run_logs(new_run_id)
                    analysis = analyze_failure(logs)
                    notify_failure(new_run_id, analysis['error_type'], analysis['error_message'])
                
                sys.exit(1)
            else:
                print(f"\n⚠️  CI run #{new_run_id} completed with status: {conclusion}")
                sys.exit(0)
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
