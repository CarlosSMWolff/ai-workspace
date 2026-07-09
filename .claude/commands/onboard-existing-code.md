---
description: Bootstrap intake by reading pre-existing code already in code/
allowed-tools: Read, Write, Edit, Bash
---
Onboard an existing codebase already sitting in `code/`:

1. Set phase to intake: `bash ai/scripts/set-phase.sh intake`.
2. Read `code/`'s README(s), dependency/lockfiles (`pyproject.toml`,
   `requirements.txt`, `environment.yml`, `package.json`, etc.), and top-level
   module/notebook structure. Don't read every file exhaustively — enough to
   draft an informed summary.
3. Draft `ai/project.md`, `ai/glossary.md`, and `ai/conventions.md` from what
   you infer (physical system, apparent central question, existing
   model/equations/data, any notation/units conventions visible in the code).
   Clearly label every inferred item "inferred from code/ — confirm or correct."
4. Then ask me only the intake questions code can't answer: goal type
   (exploratory/explanatory/pedagogical/new-result), intended audience,
   desired rigor, whether literature search is allowed, success criteria. Skip
   anything your code-reading already answered with reasonable confidence.
5. After I respond, finalize `ai/project.md`, `ai/glossary.md`,
   `ai/conventions.md`, and `ai/open-questions.md`, combining both sources.

Remember: intake phase never allows writing to `code/` — you may only read
there. Writing to `code/` is deployment-phase-only, and new development
happens in `ai/code_dev/` (development phase), not directly in `code/`.
