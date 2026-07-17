# Research Workbench (ai/)

## What this is
A wiki-style, phase-gated workspace for multi-day AI-assisted physics research.
It lives entirely under `ai/` so the rest of the repo stays clean. `code/` (at
the repo root, a sibling of `ai/`) holds the actual deployed/tested project
code — packages, notebooks, whatever structure the project needs. This
workspace never imposes a structure on `code/`.

## Core model
Four wiki layers, plus two code areas. Do not confuse them.

- `sessions/` — chronological interaction logs. What happened, including dead ends.
- `investigations/` — distilled wiki pages, one per result. What we currently believe.
- `literature/` — topic-level notes plus `references.bib`. What prior work supports.
- `simulations/` — a lightweight registry linking numerical experiments to
  investigations. It does not hold code itself, just an index row per
  experiment pointing at where the code actually lives.
- `code_dev/` (inside `ai/`) — in-progress, experimental code. No imposed
  internal structure.
- `code/` (repo root, sibling of `ai/`) — deployed/tested code, promoted from
  `code_dev/` via `/deploy-code`. No imposed internal structure.

## Global rules
- Do not invent citations, equations, results, or numerical evidence.
- Mark uncertain claims explicitly; separate assumptions from conclusions.
- Separate exact results from approximations.
- Use `$$ ... $$` for displayed equations, `$...$` for inline.
- Keep Markdown plain enough for the dashboard to render (no exotic extensions).
- When corrected on something durable, update the relevant file, not just this chat.
- This workspace deliberately skips a formal provenance/confidence-grading system.
  Use a single `Status: draft | stable` line where the templates below have one;
  don't invent extra grading fields.

## Phases — enforced, not just prompted
Switch phases with `/phase <name>`: `intake`, `session`, `literature`, `theory`,
`criticism`, `development`, `deployment`, `presentation`. This runs
`ai/scripts/set-phase.sh`, which writes `ai/state/phase.txt`.

A `PreToolUse` hook (`.claude/hooks/phase_guard.py`) reads that file plus
`ai/state/phase-rules.json` and **denies** Edit/Write/NotebookEdit calls to
files outside the current phase's allowlist. This is a real guardrail enforced
by the harness, not a convention you have to remember to follow — if a tool
call is denied, the error names the current phase and how to switch. Don't try
to work around a denial; switch phase with `/phase` instead, or explain to the
user why the current phase should be reconsidered.

Files always editable regardless of phase: `ai/state/`, `ai/sessions/`,
`ai/simulations/`, `ai/open-questions.md`, `CLAUDE.md`, `ai/CLAUDE.md`,
`.claude/`, `.gitignore`. Files outside `ai/` (deployed project code under
`code/`) are only editable in `deployment` phase — see
`ai/state/phase-rules.json` for the exact enforced prefixes.

Default phase for a new project: `intake`. Do not infer phase transitions from
conversation; only `/phase` changes them.

Summary of intent per phase:

- **intake** — understand the project before literature, theory, or code. Ask
  the user compact framing questions (physical system, central question, goal
  type, known model/equations/data, assumptions, audience, rigor, whether
  literature search is allowed, notation, success criteria). Populate
  `project.md`, `open-questions.md`, `glossary.md`, `conventions.md`. If
  `code/` already has content, use `/onboard-existing-code` instead of asking
  everything cold.
- **session** — record day-by-day exploration in `sessions/`. Distill at the
  end into `investigations/`.
- **literature** — build source-grounded topic notes in `literature/`.
  Distinguish searched / abstract-inspected / body-inspected / reused. Never
  invent citations.
- **theory** — develop distilled results in `investigations/`. State
  assumptions, derivation, exact vs. approximate steps, consistency checks,
  limiting cases, falsifiable predictions.
- **criticism** — attack the current theory/literature synthesis in
  `investigations/`. Look for hidden assumptions, sign/gauge errors,
  finite-size or boundary artifacts, numerical artifacts, overclaimed
  literature support. Output: strongest objections, what would falsify the
  claim, minimal diagnostic to check next.
- **development** — the only phase where `ai/code_dev/` may be touched. This
  is where new/experimental code gets written and iterated on. Fixed seeds,
  reproducible scripts. Register numerical experiments in
  `ai/simulations/index.md` as you go.
- **deployment** — the only phase where the repo-root `code/` may be touched.
  Normally reached via `/deploy-code`, which promotes `ai/code_dev/` into
  `code/` (additive merge — never deletes anything `code/` has that
  `code_dev/` doesn't).
- **presentation** — polish `ai/dashboard/` and the serve scripts only. Never
  change scientific content while doing this.

## File conventions

### Sessions
`sessions/YYYY-MM-DD-slug/log.md`, from `SESSION_TEMPLATE.md`. Update
`sessions/index.md` at the end. Never cite a session log as a final result.

### Investigations
One file per result: `investigations/inv-NNN-slug.md`, from
`INVESTIGATION_TEMPLATE.md`. Add a same-named folder (`figures/`, `data/`)
only when the investigation needs assets beyond text.

### Literature
Organize by topic, not by paper: `literature/topic-slug.md`, from
`TOPIC_TEMPLATE.md`, plus `literature/references.bib`. PDFs used for
inspection may be cached in `literature/pdfs/` (gitignored, not canonical —
durable knowledge belongs in the topic notes and the `.bib` file).

### Simulations (registry only)
`simulations/index.md` is a running log: one row per numerical experiment,
with its purpose, status, linked investigation, and the path into
`ai/code_dev/` or `code/` where the code actually lives. It holds no code and
no per-experiment folder template — the code's location and structure is
whatever `code_dev/`/`code/` already look like.

### Code
`ai/code_dev/` (development phase) and `code/` (deployment phase) hold
whatever the project actually needs — no scaffold-imposed layout. Use
`/deploy-code` to promote `code_dev/` into `code/`.

## Index maintenance
When creating or substantially updating a file, update its index: sessions ->
`sessions/index.md`, investigations -> `investigations/index.md`, literature
-> `literature/index.md`, simulations -> `simulations/index.md`, global nav ->
`index.md`.

## Slash commands
- `/start-project` — bootstrap a brand-new project (enters intake, asks framing questions)
- `/onboard-existing-code` — bootstrap intake by reading pre-existing code in `code/`
- `/phase <name>` — switch the active phase
- `/catch-up` — resume: read state + latest session, brief before doing anything
- `/wrap-up` — distill session, update indices, save state, commit
- `/new-session <slug>` — scaffold today's session folder
- `/new-investigation <slug>` — scaffold a new investigation page
- `/new-simulation <slug>` — register a numerical experiment in the simulations index
- `/deploy-code` — promote `ai/code_dev/` into `code/` (additive merge, deployment phase only)
- `/dashboard` — start the live dashboard server

## Current state
@state/STATE.md
