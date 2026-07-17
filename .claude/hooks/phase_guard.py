#!/usr/bin/env python3
"""PreToolUse hook: enforce ai/ phase gating on Edit/Write/NotebookEdit.

Reads the current phase from ai/state/phase.txt and the allowed-path rules
from ai/state/phase-rules.json, and denies tool calls that would edit a file
outside what the current phase permits.

Check order:
  1. always_allowed prefixes → allow unconditionally.
  2. Current phase's allowlist prefixes → allow (works for any path, inside or
     outside ai/, so phases like ai-config can whitelist .claude/ or CLAUDE.md).
  3. Path starts with ai/ → deny with a phase-specific message.
  4. Path is outside ai/ → allow only in 'deployment' phase (for code/), deny
     otherwise.

Fails open (allows the edit) if the rules/state files are missing or malformed,
so a corrupted state file can never brick the repo.
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

    # 1. Always-allowed paths (state files, session logs, etc.)
    always_allowed = rules.get("always_allowed", [])
    if any(rel_path.startswith(p) for p in always_allowed):
        return

    # 2. Current phase's explicit allowlist — checked for ALL paths, not just
    #    ai/ ones, so that ai-config can whitelist .claude/ or CLAUDE.md.
    phase_allowed = rules.get("phases", {}).get(phase, [])
    if any(rel_path.startswith(p) for p in phase_allowed):
        return

    # 3. File is inside ai/ but not allowed by this phase.
    if rel_path.startswith("ai/"):
        ai_allowed = [p for p in phase_allowed if p.startswith("ai/")]
        deny(
            f"Phase '{phase}' does not allow editing '{rel_path}'. "
            f"Allowed ai/ paths in this phase: {ai_allowed or '(none)'}. "
            f"Switch phase with /phase <name>."
        )

    # 4. File is outside ai/ (project code or repo-root config).
    #    'deployment' phase allows everything under code/; 'ai-config' handles
    #    .claude/ and CLAUDE.md via the allowlist above (already returned if
    #    matched). Anything else is blocked.
    if phase == "deployment":
        return
    deny(
        f"Editing '{rel_path}' (outside ai/) is not allowed in phase '{phase}'. "
        f"For deployed project code (code/) switch to 'deployment' phase; "
        f"for AI behaviour files (.claude/, CLAUDE.md) switch to 'ai-config' phase. "
        f"Switch with /phase <name>."
    )


if __name__ == "__main__":
    main()
