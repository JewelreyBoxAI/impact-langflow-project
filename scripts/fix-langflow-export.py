#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix corrupted Langflow JSON exports by replacing œ with proper quotes.
Usage: python fix-langflow-export.py <input.json> [output.json]
"""
import sys
import json
import re
import os

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_langflow_json(input_path, output_path=None):
    """Fix corrupted œ characters in Langflow JSON exports."""
    if output_path is None:
        output_path = input_path.replace('.json', '_fixed.json')

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Replace œ with a placeholder to avoid confusion
    content = content.replace('œ', '\x00QUOTE\x00')

    # Step 2: Find and fix the problematic edge ID patterns
    # Pattern: "id": "reactflow__edge-...[nested json]..."
    # The nested JSON needs escaped quotes
    import re

    def escape_nested_json(match):
        """Escape quotes in nested JSON within string values."""
        full_match = match.group(0)
        # Replace placeholder with escaped quotes inside the value
        fixed = full_match.replace('\x00QUOTE\x00', '\\"')
        return fixed

    # Fix edge IDs and handles that contain nested JSON
    pattern = r'"(id|sourceHandle|targetHandle)"\s*:\s*"[^"]*\x00QUOTE\x00[^"]*"'
    content = re.sub(pattern, escape_nested_json, content)

    # Step 3: Replace remaining placeholders with regular quotes
    content = content.replace('\x00QUOTE\x00', '"')

    # Validate it's proper JSON
    try:
        json.loads(content)
        print("[OK] JSON is valid after fix")
    except json.JSONDecodeError as e:
        print(f"[WARNING] JSON may still have issues: {e}")
        # Continue anyway, user can manually fix remaining issues

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] Fixed JSON written to: {output_path}")
    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix-langflow-export.py <input.json> [output.json]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    fix_langflow_json(input_file, output_file)