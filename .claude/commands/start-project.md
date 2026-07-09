---
description: Bootstrap a brand-new research project (enters intake phase)
allowed-tools: Read, Write, Edit, Bash
---
Initialize a new research project in this workspace:

1. If `code/` already has real content in it, stop and tell me to run
   `/onboard-existing-code` instead — that command reads the existing code
   before asking questions, which gives a much better intake here.
2. Run `bash ai/scripts/set-phase.sh intake`.
3. Ask me a compact set of framing questions (at most 10), covering: physical
   system; central research question; whether the goal is exploratory,
   explanatory, pedagogical, or aimed at new results; known model, Hamiltonian,
   equations, or data; allowed assumptions and approximations; intended audience;
   desired rigor; whether literature/web search is allowed; mathematical
   conventions; what would count as success.
4. Do not touch literature, theory, or code files yet — intake phase only
   allows `ai/project.md`, `ai/glossary.md`, `ai/conventions.md`, `ai/index.md`.

After I answer, update `ai/project.md`, `ai/open-questions.md`, `ai/glossary.md`,
and `ai/conventions.md`. End with a recommended next phase and the exact
`/phase <name>` command to get there.
