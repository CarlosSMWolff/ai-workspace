---
description: Switch the active research phase (enforced by the PreToolUse hook)
allowed-tools: Bash, Read
---
Switch the active phase to: $ARGUMENTS

**If the requested phase is `ai-config`:**
1. Before running anything, tell the user that `ai-config` unlocks editing of
   all AI behaviour files (`.claude/`, `CLAUDE.md`, `ai/CLAUDE.md`,
   `ai/README.md`, and the phase scripts) and ask whether they want to proceed.
2. Do NOT run the script until the user explicitly confirms.
3. Once confirmed, run `bash ai/scripts/set-phase.sh ai-config --confirmed`.

**For all other phases:**
Run `bash ai/scripts/set-phase.sh $ARGUMENTS`. If it fails because the name is
invalid, show the valid phase list from the error output.

If it succeeds, read the matching phase summary in `ai/CLAUDE.md` and give me a
one-paragraph reminder of this phase's goal and what it does and doesn't allow.
Do not start phase-specific work yet unless I ask for it.
