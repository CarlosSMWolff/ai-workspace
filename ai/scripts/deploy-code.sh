#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ai/scripts/deploy-code.sh

Additive merge: copies everything under ai/code_dev/ onto code/, overwriting
matching files/folders, but never deleting anything already in code/ that
code_dev/ doesn't have. Requires rsync.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
src="$repo_root/ai/code_dev"
dest="$repo_root/code"

if [[ ! -d "$src" ]]; then
  echo "Nothing to deploy: $src does not exist." >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but not found on PATH." >&2
  exit 1
fi

mkdir -p "$dest"
# -a (archive) without --delete: additive merge, nothing in dest is removed.
rsync -a "$src"/ "$dest"/

echo "Copied ai/code_dev/ onto code/ (additive merge, nothing deleted)."
echo
echo "Review before committing:"
git -C "$repo_root" status --short -- code 2>/dev/null || true
