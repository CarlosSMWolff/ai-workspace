---
description: End the session — distill, update indices, save state, and commit
allowed-tools: Read, Edit, Write, Bash
---
Close out this session:

1. If today's session log exists (`ai/sessions/YYYY-MM-DD-*/log.md`), fill in
   its Distillation section (updates to investigations, new claims, failed
   ideas, open questions, next session). If none exists, create one from
   `ai/sessions/SESSION_TEMPLATE.md` first.
2. Update `ai/sessions/index.md`.
3. Update `ai/open-questions.md` if anything changed.
4. Overwrite `ai/state/STATE.md` with the current phase, status, open
   questions, and next steps.
5. Stage all changes and create a git commit with a concise, descriptive
   message. Do not push.
