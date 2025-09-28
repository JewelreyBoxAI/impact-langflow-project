#!/usr/bin/env python3
"""
LangFlow Configuration Cleanup Script
Removes unnecessary placeholders and optimizes flow configuration
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_placeholders(obj: Any) -> Any:
    """Recursively remove empty placeholder fields from configuration"""
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            # Skip empty placeholder fields
            if key == "placeholder" and (value == "" or value is None):
                continue

            # Clean nested objects
            cleaned_value = clean_placeholders(value)

            # Only include non-empty values
            if cleaned_value is not None and cleaned_value != "":
                cleaned[key] = cleaned_value

        return cleaned
    elif isinstance(obj, list):
        return [clean_placeholders(item) for item in obj if item is not None]
    else:
        return obj

def optimize_component_config(component: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize individual component configuration"""
    if not isinstance(component, dict):
        return component

    # Remove redundant tool_placeholder entries
    if "data" in component and "node" in component["data"]:
        node = component["data"]["node"]

        # Clean template configuration
        if "template" in node:
            template = node["template"]

            # Remove tool_placeholder if it's not actually used
            if "tool_placeholder" in template:
                tool_placeholder = template["tool_placeholder"]
                if isinstance(tool_placeholder, dict):
                    # Check if it's just the default placeholder
                    if (tool_placeholder.get("value") == "" and
                        tool_placeholder.get("display_name") == "Tool Placeholder"):
                        logger.info(f"Removing unused tool_placeholder from component {component.get('id', 'unknown')}")
                        del template["tool_placeholder"]

            # Clean up empty value fields
            for field_name, field_config in list(template.items()):
                if isinstance(field_config, dict):
                    if field_config.get("value") == "" and field_name not in ["template"]:
                        # Keep essential fields but clean up empty values
                        if "placeholder" in field_config and field_config["placeholder"] == "":
                            del field_config["placeholder"]

    return component

def clean_langflow_configuration(file_path: str) -> bool:
    """Clean and optimize LangFlow configuration file"""
    try:
        logger.info(f"Cleaning LangFlow configuration: {file_path}")

        # Load original configuration
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        original_size = len(json.dumps(config))
        logger.info(f"Original file size: {original_size} characters")

        # Clean the configuration
        cleaned_config = clean_placeholders(config)

        # Optimize individual components
        if "data" in cleaned_config and "nodes" in cleaned_config["data"]:
            nodes = cleaned_config["data"]["nodes"]
            for i, node in enumerate(nodes):
                nodes[i] = optimize_component_config(node)

        # Create backup of original file
        backup_path = f"{file_path}.backup"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created backup at: {backup_path}")

        # Write cleaned configuration
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_config, f, indent=2, ensure_ascii=False)

        new_size = len(json.dumps(cleaned_config))
        reduction = original_size - new_size
        percentage = (reduction / original_size) * 100 if original_size > 0 else 0

        logger.info(f"Cleaned file size: {new_size} characters")
        logger.info(f"Size reduction: {reduction} characters ({percentage:.1f}%)")

        return True

    except Exception as e:
        logger.error(f"Error cleaning configuration {file_path}: {e}")
        return False

def validate_langflow_config(file_path: str) -> List[str]:
    """Validate LangFlow configuration and return any issues"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Check for required structure
        if "data" not in config:
            issues.append("Missing 'data' section")
            return issues

        data = config["data"]

        if "nodes" not in data:
            issues.append("Missing 'nodes' section")

        if "edges" not in data:
            issues.append("Missing 'edges' section")

        # Validate nodes
        if "nodes" in data:
            nodes = data["nodes"]
            if not isinstance(nodes, list):
                issues.append("'nodes' should be a list")
            else:
                for i, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        issues.append(f"Node {i} is not a dictionary")
                        continue

                    if "id" not in node:
                        issues.append(f"Node {i} missing 'id' field")

                    if "data" not in node:
                        issues.append(f"Node {i} missing 'data' field")

        # Validate edges
        if "edges" in data:
            edges = data["edges"]
            if not isinstance(edges, list):
                issues.append("'edges' should be a list")
            else:
                for i, edge in enumerate(edges):
                    if not isinstance(edge, dict):
                        issues.append(f"Edge {i} is not a dictionary")
                        continue

                    required_edge_fields = ["id", "source", "target"]
                    for field in required_edge_fields:
                        if field not in edge:
                            issues.append(f"Edge {i} missing '{field}' field")

        logger.info(f"Configuration validation complete: {len(issues)} issues found")

    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON format: {e}")
    except Exception as e:
        issues.append(f"Validation error: {e}")

    return issues

def main():
    """Main cleanup function"""
    flows_directory = Path("C:/AI_src/ImpactLangFlow/flows")

    if not flows_directory.exists():
        logger.error(f"Flows directory not found: {flows_directory}")
        return

    # Find all JSON flow files
    flow_files = list(flows_directory.glob("*.json"))

    if not flow_files:
        logger.warning("No JSON flow files found")
        return

    logger.info(f"Found {len(flow_files)} flow files to process")

    cleaned_count = 0

    for flow_file in flow_files:
        logger.info(f"\nProcessing: {flow_file.name}")

        # Validate before cleaning
        issues = validate_langflow_config(str(flow_file))
        if issues:
            logger.warning(f"Validation issues in {flow_file.name}:")
            for issue in issues[:5]:  # Show first 5 issues
                logger.warning(f"  - {issue}")

        # Clean the configuration
        if clean_langflow_configuration(str(flow_file)):
            cleaned_count += 1

            # Validate after cleaning
            post_issues = validate_langflow_config(str(flow_file))
            if len(post_issues) < len(issues):
                logger.info(f"✅ Fixed {len(issues) - len(post_issues)} validation issues")
            elif post_issues:
                logger.warning(f"⚠️ {len(post_issues)} validation issues remain")
            else:
                logger.info("✅ Configuration is valid")
        else:
            logger.error(f"❌ Failed to clean {flow_file.name}")

    logger.info(f"\n🎉 Cleanup complete: {cleaned_count}/{len(flow_files)} files processed successfully")

if __name__ == "__main__":
    main()