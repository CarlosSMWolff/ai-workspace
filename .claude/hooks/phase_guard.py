#!/usr/bin/env python3
"""PreToolUse hook: enforce ai/ phase gating on Edit/Write/NotebookEdit.

Reads the current phase from ai/state/phase.txt and the allowed-path rules
from ai/state/phase-rules.json, and denies tool calls that would edit a file
outside what the current phase permits. Files inside ai/ are checked against
the phase's allowlist; files outside ai/ (i.e. deployed project code under
code/) are only editable during the 'deployment' phase — in-progress code
belongs in ai/code_dev/ instead, promoted to code/ via /deploy-code. Fails
open (allows the edit) if the rules/state files are missing or malformed, so a
corrupted state file can never brick the repo.
"""
import json
import os
import sys


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return

    cwd = data.get("cwd") or os.getcwd()
    rel_path = os.path.relpath(file_path, cwd).replace(os.sep, "/")

    rules = load_json(os.path.join(cwd, "ai", "state", "phase-rules.json"))
    if rules is None:
        return  # fail open: no rules file present

    phase_file = os.path.join(cwd, "ai", "state", "phase.txt")
    try:
        with open(phase_file) as f:
            phase = f.read().strip() or "intake"
    except OSError:
        phase = "intake"

    always_allowed = rules.get("always_allowed", [])
    if any(rel_path.startswith(p) for p in always_allowed):
        return

    if rel_path.startswith("ai/"):
        allowed = rules.get("phases", {}).get(phase, [])
        if any(rel_path.startswith(p) for p in allowed):
            return
        deny(
            f"Phase '{phase}' does not allow editing '{rel_path}'. "
            f"Allowed ai/ paths in this phase: {allowed or '(none)'}. "
            f"Switch phase with /phase <name>."
        )
    else:
        if phase == "deployment":
            return
        deny(
            f"Editing project code ('{rel_path}') requires DEPLOYMENT phase "
            f"(current phase: '{phase}'). In-progress code belongs in "
            f"ai/code_dev/ instead (writable in 'development' phase); promote "
            f"it to code/ with /deploy-code once ready. Switch with "
            f"/phase deployment."
        )


if __name__ == "__main__":
    main()
