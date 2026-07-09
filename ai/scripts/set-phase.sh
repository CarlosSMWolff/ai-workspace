#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ai/scripts/set-phase.sh PHASE

Valid phases:
  intake session literature theory criticism development deployment presentation

This writes ai/state/phase.txt, which the PreToolUse hook
(.claude/hooks/phase_guard.py) reads to decide which files may be edited.
EOF
}

VALID_PHASES=(intake session literature theory criticism development deployment presentation)

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

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
state_dir="$repo_root/ai/state"
mkdir -p "$state_dir"

echo "$phase" > "$state_dir/phase.txt"
echo "$(date +"%Y-%m-%d %H:%M") -> $phase" >> "$state_dir/phase-history.log"

echo "Phase set to: $phase"
