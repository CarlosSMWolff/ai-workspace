#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ai/scripts/set-phase.sh PHASE [--confirmed]

Valid phases:
  ai-config intake session literature theory criticism development deployment presentation

Note: switching to 'ai-config' requires the --confirmed flag.
The /phase command will ask for explicit user confirmation before passing it.

This writes ai/state/phase.txt, which the PreToolUse hook
(.claude/hooks/phase_guard.py) reads to decide which files may be edited.
EOF
}

VALID_PHASES=(ai-config intake session literature theory criticism development deployment presentation)

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || -z "${1:-}" ]]; then
  usage
  exit 0
fi

phase="$1"
valid=0
for p in "${VALID_PHASES[@]}"; do
  [[ "$p" == "$phase" ]] && valid=1
done

if [[ "$valid" -eq 0 ]]; then
  echo "Invalid phase: $phase" >&2
  usage >&2
  exit 2
fi

# Hard lock: ai-config requires explicit --confirmed flag so the /phase command
# is forced to ask the user before proceeding.
if [[ "$phase" == "ai-config" ]]; then
  confirmed=0
  for arg in "${@:2}"; do
    [[ "$arg" == "--confirmed" ]] && confirmed=1
  done
  if [[ "$confirmed" -eq 0 ]]; then
    echo "ERROR: 'ai-config' modifies AI behaviour files (.claude/, CLAUDE.md, ai/CLAUDE.md, ai/README.md)." >&2
    echo "Explicit user confirmation is required. The /phase command will ask before proceeding." >&2
    echo "To bypass (not recommended): bash ai/scripts/set-phase.sh ai-config --confirmed" >&2
    exit 3
  fi
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
state_dir="$repo_root/ai/state"
mkdir -p "$state_dir"

echo "$phase" > "$state_dir/phase.txt"
echo "$(date +"%Y-%m-%d %H:%M") -> $phase" >> "$state_dir/phase-history.log"

echo "Phase set to: $phase"
