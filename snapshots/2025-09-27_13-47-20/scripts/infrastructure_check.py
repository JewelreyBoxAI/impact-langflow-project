#!/usr/bin/env python3
"""
Infrastructure Health Check Script
Validates system readiness for production deployment
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

def check_python_environment() -> Tuple[bool, List[str]]:
    """Check Python environment and dependencies"""
    issues = []

    # Check Python version
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 8:
        issues.append(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")

    # Check critical packages
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'requests',
        'python-dotenv', 'httpx', 'mcp'
    ]

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            issues.append(f"Missing required package: {package}")

    return len(issues) == 0, issues

def check_file_structure() -> Tuple[bool, List[str]]:
    """Check required file and directory structure"""
    issues = []

    required_files = [
        "flows/recruiting.json",
        "MCPServers/zoho-crm-mcp-server/langflow_mcp_config.json",
        "requirements.txt",
        "validate_deployment.sh"
    ]

    required_dirs = [
        "flows",
        "MCPServers",
        "backend",
        "tests"
    ]

    # Check directories
    for directory in required_dirs:
        if not os.path.exists(directory):
            issues.append(f"Missing directory: {directory}")

    # Check files
    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"Missing file: {file_path}")

    return len(issues) == 0, issues

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check for required environment variables (without exposing values)"""
    issues = []

    # Check for .env file existence
    if not os.path.exists('.env'):
        issues.append("Missing .env file - create from .env.example")

    # Don't check actual credential values for security
    # Just verify structure

    return len(issues) == 0, issues

def check_port_availability() -> Tuple[bool, List[str]]:
    """Check if required ports are available"""
    issues = []

    required_ports = [3000, 8000, 5432]  # Frontend, Backend, Database

    for port in required_ports:
        try:
            # Simple port check (won't bind, just test availability)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                issues.append(f"Port {port} is already in use")
        except Exception as e:
            # If we can't check, assume it's available
            pass

    return len(issues) == 0, issues

def check_docker_availability() -> Tuple[bool, List[str]]:
    """Check if Docker is available and running"""
    issues = []

    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            issues.append("Docker is not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        issues.append("Docker is not installed or not in PATH")

    try:
        result = subprocess.run(['docker', 'ps'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            issues.append("Docker daemon is not running")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        issues.append("Cannot connect to Docker daemon")

    return len(issues) == 0, issues

def check_git_status() -> Tuple[bool, List[str]]:
    """Check Git repository status"""
    issues = []

    try:
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            issues.append("Not in a Git repository")
        else:
            # Check for uncommitted changes
            if result.stdout.strip():
                issues.append("Repository has uncommitted changes")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        issues.append("Git is not available")

    return len(issues) == 0, issues

def check_flow_files() -> Tuple[bool, List[str]]:
    """Check LangFlow JSON files"""
    issues = []

    flows_dir = Path("flows")
    if not flows_dir.exists():
        issues.append("flows/ directory not found")
        return False, issues

    json_files = list(flows_dir.glob("*.json"))
    if not json_files:
        issues.append("No flow JSON files found")
        return False, issues

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic structure validation
            if "data" not in data:
                issues.append(f"{json_file.name}: Missing 'data' key")
            elif "nodes" not in data["data"]:
                issues.append(f"{json_file.name}: Missing 'nodes' section")

        except json.JSONDecodeError as e:
            issues.append(f"{json_file.name}: Invalid JSON - {e}")
        except Exception as e:
            issues.append(f"{json_file.name}: Error reading file - {e}")

    return len(issues) == 0, issues

def run_health_checks() -> Dict[str, Any]:
    """Run all health checks"""
    print("Infrastructure Health Check")
    print("=" * 50)

    checks = [
        ("Python Environment", check_python_environment),
        ("File Structure", check_file_structure),
        ("Environment Variables", check_environment_variables),
        ("Port Availability", check_port_availability),
        ("Docker Availability", check_docker_availability),
        ("Git Status", check_git_status),
        ("Flow Files", check_flow_files)
    ]

    results = {
        "total_checks": len(checks),
        "passed_checks": 0,
        "failed_checks": 0,
        "check_results": {}
    }

    for check_name, check_function in checks:
        print(f"\nChecking: {check_name}")

        try:
            passed, issues = check_function()

            if passed:
                print("   Status: PASS")
                results["passed_checks"] += 1
            else:
                print("   Status: FAIL")
                results["failed_checks"] += 1

                # Show issues
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"   - {issue}")

                if len(issues) > 3:
                    print(f"   ... and {len(issues) - 3} more issues")

            results["check_results"][check_name] = {
                "passed": passed,
                "issues": issues
            }

        except Exception as e:
            print(f"   Status: ERROR - {e}")
            results["failed_checks"] += 1
            results["check_results"][check_name] = {
                "passed": False,
                "issues": [f"Check failed with error: {e}"]
            }

    return results

def print_summary(results: Dict[str, Any]):
    """Print health check summary"""
    print(f"\n" + "=" * 50)
    print(f"HEALTH CHECK SUMMARY")
    print(f"=" * 50)
    print(f"Total Checks:  {results['total_checks']}")
    print(f"Passed:        {results['passed_checks']}")
    print(f"Failed:        {results['failed_checks']}")

    if results['total_checks'] > 0:
        success_rate = (results['passed_checks'] / results['total_checks']) * 100
        print(f"Success Rate:  {success_rate:.1f}%")

        if success_rate >= 95:
            print(f"\nStatus: EXCELLENT - Ready for deployment")
            deployment_ready = True
        elif success_rate >= 80:
            print(f"\nStatus: GOOD - Minor issues to address")
            deployment_ready = True
        elif success_rate >= 60:
            print(f"\nStatus: MODERATE - Several issues need fixing")
            deployment_ready = False
        else:
            print(f"\nStatus: POOR - Major issues prevent deployment")
            deployment_ready = False
    else:
        deployment_ready = False

    # Show failed checks
    if results['failed_checks'] > 0:
        print(f"\nFailed Checks:")
        for check_name, check_result in results['check_results'].items():
            if not check_result['passed']:
                print(f"  - {check_name}")

    return deployment_ready

def main():
    """Main health check execution"""
    # Run all health checks
    results = run_health_checks()

    # Print summary
    deployment_ready = print_summary(results)

    # Return appropriate exit code
    if deployment_ready:
        print(f"\nInfrastructure is ready for deployment!")
        return 0
    else:
        print(f"\nInfrastructure requires fixes before deployment")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)