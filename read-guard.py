#!/usr/bin/env python3
"""
PreToolUse hook for Read tool - Enforce offset/limit and block large file reads.

Rules:
1. Files exceeding EITHER line OR byte threshold MUST use offset + limit parameters
2. Single read limit: 500 lines OR 20KB max
3. Suggests using Grep to locate targets first

Exit codes:
- 0: Success (with JSON output for control)
- 2: Block operation (stderr message shown to Claude)
"""
import json
import sys
import os
from datetime import datetime

# Configuration - Dual Threshold Design
MAX_FILE_LINES = 1000           # Line count threshold
MAX_FILE_BYTES = 50 * 1024      # 50KB byte threshold
MAX_SINGLE_READ_LINES = 500     # Maximum lines per read operation
MAX_SINGLE_READ_BYTES = 20 * 1024  # 20KB per read operation

SKIP_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf', '.exe', '.dll', '.so', '.dylib'}

# Statistics log file
LOG_FILE = os.path.expandvars("$USERPROFILE/.claude/hooks/read-stats.log")


def get_file_line_count(file_path):
    """Get total line count of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return None


def get_file_size(file_path):
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return None


def log_stats(file_path, lines, bytes_size, blocked, reason=""):
    """Log read attempts for analysis and tuning."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "BLOCKED" if blocked else "ALLOWED"
        log_entry = f"{timestamp} | {status} | lines={lines} bytes={bytes_size} | {reason} | {file_path}\n"
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass  # Logging failure should not affect hook operation


def format_bytes(size):
    """Format bytes to human readable string."""
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    elif size >= 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size}B"


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[Hook Error] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Read tool
    if tool_name != "Read":
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    offset = tool_input.get("offset")
    limit = tool_input.get("limit")

    # Skip binary files
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        sys.exit(0)

    # Check if file exists
    if not os.path.exists(file_path):
        sys.exit(0)  # Let the tool handle missing file error

    # Get file metrics
    file_lines = get_file_line_count(file_path)
    file_bytes = get_file_size(file_path)

    if file_lines is None or file_bytes is None:
        sys.exit(0)  # Cannot read, let tool handle it

    # Rule 1: Large files (exceeding EITHER threshold) MUST specify offset and limit
    exceeds_lines = file_lines > MAX_FILE_LINES
    exceeds_bytes = file_bytes > MAX_FILE_BYTES

    if exceeds_lines or exceeds_bytes:
        if offset is None or limit is None:
            reason_parts = []
            if exceeds_lines:
                reason_parts.append(f"{file_lines} lines (>{MAX_FILE_LINES})")
            if exceeds_bytes:
                reason_parts.append(f"{format_bytes(file_bytes)} (>{format_bytes(MAX_FILE_BYTES)})")
            reason = " AND ".join(reason_parts)

            error_msg = (
                f"BLOCKED: File exceeds thresholds: {reason}.\n"
                f"You MUST specify both 'offset' and 'limit' parameters.\n\n"
                f"Recommended approach:\n"
                f"1. Use Grep to find target line numbers first\n"
                f"2. Then Read with offset and limit (max {MAX_SINGLE_READ_LINES} lines / {format_bytes(MAX_SINGLE_READ_BYTES)})\n\n"
                f"Example:\n"
                f"  Grep: pattern=\"function_name\" path=\"{file_path}\"\n"
                f"  Read: file_path=\"{file_path}\", offset=<line-5>, limit=50"
            )
            log_stats(file_path, file_lines, file_bytes, blocked=True, reason=f"missing offset/limit: {reason}")
            print(error_msg, file=sys.stderr)
            sys.exit(2)

    # Rule 2: Check if requested read range is too large (lines)
    if limit is not None and limit > MAX_SINGLE_READ_LINES:
        error_msg = (
            f"BLOCKED: Requested limit={limit} exceeds maximum {MAX_SINGLE_READ_LINES} lines.\n"
            f"Please reduce the limit parameter to {MAX_SINGLE_READ_LINES} or less."
        )
        log_stats(file_path, file_lines, file_bytes, blocked=True, reason=f"limit too large: {limit}")
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    # Rule 3: If offset is specified but limit is not, auto-add limit
    if offset is not None and limit is None:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"Auto-added limit={MAX_SINGLE_READ_LINES} (file: {file_lines} lines, {format_bytes(file_bytes)})",
                "updatedInput": {
                    "limit": MAX_SINGLE_READ_LINES
                }
            }
        }
        log_stats(file_path, file_lines, file_bytes, blocked=False, reason="auto-added limit")
        print(json.dumps(output))
        sys.exit(0)

    # All checks passed
    log_stats(file_path, file_lines, file_bytes, blocked=False, reason="passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
