#!/usr/bin/env python3
"""
LangFlow JSON Compatibility Validation Script
Validates flow JSON files for LangFlow 1.5.1 compatibility
"""

import json
import os
import sys
from typing import Dict, List, Any, Tuple
from pathlib import Path

def validate_flow_schema(flow_data: Dict[str, Any], flow_name: str) -> Tuple[bool, List[str]]:
    """Validate flow JSON against LangFlow 1.5.1 schema"""
    issues = []

    # Check required top-level structure
    if "data" not in flow_data:
        issues.append("Missing 'data' key at root level")
        return False, issues

    data = flow_data["data"]

    # Check for required sections
    required_sections = ["nodes", "edges"]
    for section in required_sections:
        if section not in data:
            issues.append(f"Missing required section: {section}")

    # Validate nodes
    if "nodes" in data:
        node_issues = validate_nodes(data["nodes"])
        issues.extend([f"Node: {issue}" for issue in node_issues])

    # Validate edges
    if "edges" in data:
        edge_issues = validate_edges(data["edges"])
        issues.extend([f"Edge: {issue}" for issue in edge_issues])

    # Check for component compatibility
    if "nodes" in data:
        compat_issues = check_component_compatibility(data["nodes"])
        issues.extend([f"Compatibility: {issue}" for issue in compat_issues])

    is_valid = len(issues) == 0
    return is_valid, issues

def validate_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    """Validate node structure and components"""
    issues = []

    for i, node in enumerate(nodes):
        node_id = node.get("id", f"node_{i}")

        # Check required node fields
        required_fields = ["data", "id", "type"]
        for field in required_fields:
            if field not in node:
                issues.append(f"{node_id}: Missing required field '{field}'")

        # Validate node data
        if "data" in node and "node" in node["data"]:
            node_data = node["data"]["node"]

            # Check component type and compatibility
            component_type = node_data.get("key", "Unknown")
            lf_version = node_data.get("lf_version", "Unknown")

            if lf_version and lf_version != "1.5.1":
                issues.append(f"{node_id}: Component version {lf_version} may not be compatible with LangFlow 1.5.1")

            # Check for legacy components
            legacy_components = {
                "HTTPTool": "Use APIRequest instead",
                "OpenAIModel": "Use LanguageModelComponent instead",
                "Prompt": "Use PromptTemplate instead",
                "PythonCode": "Use PythonREPLComponent instead",
                "PostgreSQL": "Use SQLComponent instead"
            }

            if component_type in legacy_components:
                issues.append(f"{node_id}: Legacy component '{component_type}' - {legacy_components[component_type]}")

    return issues

def validate_edges(edges: List[Dict[str, Any]]) -> List[str]:
    """Validate edge connections"""
    issues = []

    for i, edge in enumerate(edges):
        edge_id = edge.get("id", f"edge_{i}")

        # Check required edge fields
        required_fields = ["source", "target", "sourceHandle", "targetHandle"]
        for field in required_fields:
            if field not in edge:
                issues.append(f"{edge_id}: Missing required field '{field}'")

        # Validate handle structure
        if "data" in edge:
            edge_data = edge["data"]
            if "sourceHandle" in edge_data and "targetHandle" in edge_data:
                source_handle = edge_data["sourceHandle"]
                target_handle = edge_data["targetHandle"]

                # Check handle completeness
                if not isinstance(source_handle, dict) or not isinstance(target_handle, dict):
                    issues.append(f"{edge_id}: Invalid handle structure")

    return issues

def check_component_compatibility(nodes: List[Dict[str, Any]]) -> List[str]:
    """Check for LangFlow 1.5.1 specific compatibility issues"""
    issues = []

    # Track component types and connections
    component_counts = {}

    for node in nodes:
        if "data" in node and "node" in node["data"]:
            node_data = node["data"]["node"]
            component_type = node_data.get("key", "Unknown")

            component_counts[component_type] = component_counts.get(component_type, 0) + 1

    # Report component usage
    modern_components = [
        "ChatInput", "ChatOutput", "APIRequest", "LanguageModelComponent",
        "PromptTemplate", "PythonREPLComponent", "SQLComponent", "Agent", "MCPServer"
    ]

    for component_type, count in component_counts.items():
        if component_type in modern_components:
            issues.append(f"Using modern component: {component_type} (x{count})")
        else:
            issues.append(f"Unknown/Custom component: {component_type} (x{count}) - verify compatibility")

    return issues

def validate_all_flows() -> Dict[str, Any]:
    """Validate all flow files in the flows directory"""
    flows_dir = Path("flows")
    results = {
        "total_flows": 0,
        "valid_flows": 0,
        "invalid_flows": 0,
        "flow_results": {}
    }

    if not flows_dir.exists():
        print("flows/ directory not found")
        return results

    json_files = list(flows_dir.glob("*.json"))
    results["total_flows"] = len(json_files)

    print(f"Validating {len(json_files)} flow files for LangFlow 1.5.1 compatibility...")
    print("=" * 70)

    for json_file in json_files:
        flow_name = json_file.name
        print(f"\nValidating: {flow_name}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)

            is_valid, issues = validate_flow_schema(flow_data, flow_name)

            if is_valid:
                print(f"   Status: VALID")
                results["valid_flows"] += 1
            else:
                print(f"   Status: INVALID")
                results["invalid_flows"] += 1

                # Show first few issues
                for issue in issues[:5]:
                    print(f"   - {issue}")

                if len(issues) > 5:
                    print(f"   ... and {len(issues) - 5} more issues")

            results["flow_results"][flow_name] = {
                "valid": is_valid,
                "issues": issues
            }

        except json.JSONDecodeError as e:
            print(f"   Status: JSON ERROR")
            print(f"   - Invalid JSON: {e}")
            results["invalid_flows"] += 1
            results["flow_results"][flow_name] = {
                "valid": False,
                "issues": [f"JSON decode error: {e}"]
            }
        except Exception as e:
            print(f"   Status: ERROR")
            print(f"   - Validation error: {e}")
            results["invalid_flows"] += 1
            results["flow_results"][flow_name] = {
                "valid": False,
                "issues": [f"Validation error: {e}"]
            }

    return results

def print_summary(results: Dict[str, Any]):
    """Print validation summary"""
    print(f"\n" + "=" * 70)
    print(f"VALIDATION SUMMARY")
    print(f"=" * 70)
    print(f"Total Flows:   {results['total_flows']}")
    print(f"Valid Flows:   {results['valid_flows']}")
    print(f"Invalid Flows: {results['invalid_flows']}")

    if results['total_flows'] > 0:
        success_rate = (results['valid_flows'] / results['total_flows']) * 100
        print(f"Success Rate:  {success_rate:.1f}%")

        if success_rate >= 90:
            print(f"\nStatus: EXCELLENT - Ready for LangFlow 1.5.1")
        elif success_rate >= 75:
            print(f"\nStatus: GOOD - Minor issues to address")
        elif success_rate >= 50:
            print(f"\nStatus: MODERATE - Several issues need fixing")
        else:
            print(f"\nStatus: POOR - Major compatibility issues")

    # Show invalid flows
    if results['invalid_flows'] > 0:
        print(f"\nFlows requiring attention:")
        for flow_name, flow_result in results['flow_results'].items():
            if not flow_result['valid']:
                print(f"  - {flow_name}")

def main():
    """Main validation execution"""
    print("LangFlow 1.5.1 Compatibility Validation")
    print("=" * 70)

    # Validate all flows
    results = validate_all_flows()

    # Print summary
    print_summary(results)

    return results

if __name__ == "__main__":
    results = main()

    # Exit with appropriate code
    if results['invalid_flows'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)