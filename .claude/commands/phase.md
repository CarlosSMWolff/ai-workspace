---
description: Switch the active research phase (enforced by the PreToolUse hook)
allowed-tools: Bash, Read
---
Switch the active phase to: $ARGUMENTS

Run `bash ai/scripts/set-phase.sh $ARGUMENTS`. If it fails because the name is
invalid, show the valid phase list from the error output.

If it succeeds, read the matching phase summary in `ai/CLAUDE.md` and give me a
one-paragraph reminder of this phase's goal and what it does and doesn't allow.
Do not start phase-specific work yet unless I ask for it.
