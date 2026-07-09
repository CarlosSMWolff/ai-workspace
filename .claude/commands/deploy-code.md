---
description: Promote ai/code_dev/ into deployed code/ (additive merge, deployment phase only)
allowed-tools: Bash, Read
---
Promote the current `ai/code_dev/` contents into `code/`:

1. Check the current phase (`ai/state/phase.txt`). If it isn't `deployment`,
   tell me to run `/phase deployment` first and stop — do not run the script.
2. Run `bash ai/scripts/deploy-code.sh`. This performs an additive merge:
   files/folders present in `ai/code_dev/` are copied into `code/`
   (overwriting matching paths), but nothing already in `code/` that
   `code_dev/` doesn't have is touched or deleted.
3. Show me the resulting `git status --short -- code` output and summarize
   what changed. Do not commit — let me review the diff first.
