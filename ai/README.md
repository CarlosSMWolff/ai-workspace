# ai-workspace — a git-based, phase-gated research scaffold for Claude Code

This is a self-contained AI-research-workflow scaffold. Its own repo root is
`CLAUDE.md`, `.claude/`, and this `ai/` folder — everything AI-workflow-specific
lives under `ai/`, so a real project built from it stays clean:

```
your-project/            (a real git repo)
├── CLAUDE.md              # one line: @ai/CLAUDE.md
├── .claude/                # hidden: commands, the phase hook, settings
├── code/                   # deployed/tested project code — no imposed layout
└── ai/                     # everything in this scaffold
    ├── CLAUDE.md
    ├── README.md            (this file)
    ├── state/
    ├── sessions/
    ├── investigations/
    ├── literature/
    ├── simulations/         (a registry, not code)
    ├── code_dev/            # in-progress code — no imposed layout
    ├── dashboard/
    └── scripts/
```

It combines two ideas:

- A **wiki** for research knowledge (`sessions/`, `investigations/`,
  `literature/`, `simulations/`) — one page per distilled result, browsable via
  a live local dashboard — adapted from Juanjo García Ripoll's
  `ai-research-workspace` template.
- **Enforced phase gating** — a Claude Code `PreToolUse` hook that actually
  blocks edits to files outside what the current research phase allows,
  instead of relying on the model to remember a convention. This includes a
  hard wall between in-progress code (`ai/code_dev/`, writable only in
  `development` phase) and deployed code (`code/`, writable only in
  `deployment` phase).

---

## Bootstrapping a new project

This scaffold's own repo is meant to be marked as a **GitHub template
repository**. Click "Use this template" on GitHub to get a brand-new,
independent repo with `CLAUDE.md`, `.claude/`, and `ai/` already in place — no
shared git history with the template, nothing to strip out. Then:

```bash
claude
```

```text
/start-project
```

Claude sets the phase to `intake`, asks a compact set of framing questions
(physical system, central question, goal type, known model/equations/data,
assumptions, audience, rigor, whether literature search is allowed, notation,
success criteria), then populates `ai/project.md`, `ai/open-questions.md`,
`ai/glossary.md`, and `ai/conventions.md` from your answers, and recommends the
next phase.

## Bootstrapping into an existing repo (code already exists)

There's no single GitHub button for merging a template into an existing repo.
The straightforward way:

```bash
# Clone the scaffold somewhere scratch, strip its git history.
git clone https://github.com/you/ai-workspace.git /tmp/ai-workspace-scratch
rm -rf /tmp/ai-workspace-scratch/.git

# Copy the three pieces into your existing repo's root.
cp -r /tmp/ai-workspace-scratch/ai ./ai
cp /tmp/ai-workspace-scratch/CLAUDE.md ./CLAUDE.md
cp -r /tmp/ai-workspace-scratch/.claude ./.claude
chmod +x ai/scripts/*.sh ai/scripts/*.py .claude/hooks/*.py

# Commit as part of your existing repo's own history.
git add CLAUDE.md .claude ai
git commit -m "Add ai-workspace scaffold"
```

(If you expect to pull in template updates often, `git subtree add --prefix=ai
<template-url> main --squash` is a fancier alternative that keeps a pullable
relationship — more power, more ceremony. The plain copy above is the default.)

If your existing code lives somewhere other than `code/` at the repo root,
move it there first — the phase hook expects deployed code specifically at
`code/`.

Then:

```text
/onboard-existing-code
```

instead of `/start-project` — it reads `code/`'s README, dependency files, and
structure first, drafts an intake from what it infers, and only asks you the
questions the code can't answer.

## Resume an existing project (new session, same or different machine)

```bash
git pull
claude
```

```text
/catch-up
```

Claude reads `ai/state/STATE.md`, the current phase, and the latest session
log, and briefs you on where things stand and what's next — without touching
any files.

## The daily ritual

1. **Arrive** → `git pull` (if switching machines).
2. **Start** → `/catch-up`.
3. **Work** in whatever phase is active. If a tool call gets denied because the
   phase doesn't allow it, that's the hook working as intended — either switch
   phase (`/phase <name>`) or reconsider whether you're trying to do the right
   thing right now.
4. **Log as you go** — `/new-session <slug>` to start today's log,
   `/new-investigation <slug>` when a result is worth distilling,
   `/new-simulation <slug>` to register a numerical experiment.
5. **End** → `/wrap-up` (distills the session, updates indices, saves
   `STATE.md`, commits — does not push).
6. **Leave** → `git push`.

## Phases

Switch with `/phase <name>`. Valid names: `intake`, `session`, `literature`,
`theory`, `criticism`, `development`, `deployment`, `presentation`. Phase
transitions are never inferred — only `/phase` changes the active phase, and
the change is enforced by a hook (see below), not just remembered by the model.

| Phase | Goal | What it unlocks |
|---|---|---|
| `intake` (default) | Frame the project before doing anything else | `project.md`, `glossary.md`, `conventions.md`, `index.md` |
| `session` | Record day-by-day exploration | `investigations/` (for linking/updating while logging) |
| `literature` | Build source-grounded topic notes | `literature/` |
| `theory` | Develop distilled analytical results | `investigations/` |
| `criticism` | Attack the current theory/literature synthesis | `investigations/` |
| `development` | Write/iterate in-progress code | `ai/code_dev/`, `investigations/` |
| `deployment` | Promote tested code to the real repo | **`code/` (repo root, outside `ai/`)**, `investigations/` |
| `presentation` | Polish the live dashboard | `dashboard/`, the serve scripts |

`ai/state/`, `ai/sessions/`, `ai/simulations/`, `ai/open-questions.md`,
`CLAUDE.md`, and `.claude/` are always editable, in any phase.

**The important one:** anything outside `ai/` — i.e. your real deployed code in
`code/` — can only be edited during `deployment` phase. New development
happens inside `ai/code_dev/` instead (`development` phase), and gets promoted
across with `/deploy-code`. That split is the literal implementation of "don't
let the agent touch shipped code before it's actually ready."

## The code_dev → code pipeline

- `ai/code_dev/` — in-progress, experimental code. No imposed structure.
  Writable only in `development` phase.
- `code/` (repo root) — deployed/tested code, whatever layout the project
  needs (`src/`, `notebooks/`, `README.md`, `results/`, ...). Writable only in
  `deployment` phase.
- `/deploy-code` — promotes `ai/code_dev/` into `code/` via `ai/scripts/deploy-code.sh`,
  an **additive merge** (`rsync -a` without `--delete`): files/folders present in
  `code_dev/` are copied over, but nothing already in `code/` that `code_dev/`
  doesn't have (a `LICENSE`, a CI config, packaging files) is ever deleted. It
  stops after copying — review `git status`/`git diff` yourself before
  committing.

## How the enforcement actually works

`.claude/settings.json` registers `.claude/hooks/phase_guard.py` as a
`PreToolUse` hook on `Edit`, `Write`, and `NotebookEdit`. Before any such call
runs, the hook:

1. Reads `ai/state/phase.txt` for the current phase.
2. Reads `ai/state/phase-rules.json` for the allowed path prefixes.
3. Denies the call (with a reason naming the current phase and how to switch)
   if the target file isn't covered by an always-allowed prefix, the current
   phase's `ai/`-relative allowlist, or — for anything outside `ai/` — the
   `deployment`-phase exception.

This is enforced by Claude Code's hook mechanism, not by the model choosing to
comply — a denied edit is technically blocked before it happens. If the rules
or state files are ever missing or malformed, the hook fails **open** (allows
the edit) rather than bricking the workspace; it's a guardrail, not a lock you
can get permanently stuck behind.

To change the rules (e.g. add a new always-allowed path, or let `criticism`
phase touch something new), edit `ai/state/phase-rules.json` directly — no
need to touch the hook script.

## The wiki

- `sessions/` — chronological logs (`sessions/YYYY-MM-DD-slug/log.md`). What
  happened, including dead ends. Never cite a session as a final result.
- `investigations/` — one page per distilled result
  (`investigations/inv-NNN-slug.md`). What we currently believe. Each has a
  single `Status: draft | stable` line — deliberately no heavier
  confidence/provenance grading system than that.
- `literature/` — one page per topic (`literature/topic-slug.md`) plus a
  shared `references.bib`. What prior work supports, with a claims matrix
  tying each claim to its source.
- `simulations/` — a **registry**, not code. One row per numerical experiment
  in `simulations/index.md`: purpose, linked investigation, the path in
  `ai/code_dev/`/`code/` where the code actually lives, and status. Register
  every experiment immediately — unregistered ones are invisible in the
  dashboard even though the files exist on disk.

Update the matching `index.md` whenever you create or substantially change a
page in that folder.

## The live dashboard

```text
/dashboard
```

or directly:

```bash
python3 ai/scripts/serve.py
```

Then open `http://127.0.0.1:8000/`. It's a small stdlib HTTP server (no
dependencies, no build step) that renders the wiki's Markdown (with MathJax
equations), figures, and source files — including `ai/code_dev/` — in a
browser, auto-refreshing while it runs. The URL mirrors paths inside `ai/` —
e.g. `http://127.0.0.1:8000/investigations/inv-001-example.md`. Good for
showing live progress in a talk; it is a visualization layer, not the source
of truth — always edit the Markdown, not the dashboard's rendering of it.

## Slash commands

| Command | Does |
|---|---|
| `/start-project` | Bootstrap a brand-new project, enters `intake` phase |
| `/onboard-existing-code` | Bootstrap intake by reading pre-existing code in `code/` |
| `/phase <name>` | Switch the active (enforced) phase |
| `/catch-up` | Resume: brief on current state, don't touch files |
| `/wrap-up` | Distill session, update indices, save state, commit |
| `/new-session <slug>` | Scaffold today's session log |
| `/new-investigation <slug>` | Scaffold a new investigation page |
| `/new-simulation <slug>` | Register a numerical experiment in the simulations index |
| `/deploy-code` | Promote `ai/code_dev/` into `code/` (additive merge, `deployment` phase only) |
| `/dashboard` | Start the live dashboard server |

## Updating this workspace from a newer template version

There's no branch relationship to diff once a project is bootstrapped (a
GitHub-template-spawned repo has independent history; a manually-vendored one
never had one). To pull in template improvements later, clone the template
fresh into a scratch folder and manually copy/diff the specific files you
want — usually `ai/scripts/`, `ai/dashboard/`, `ai/CLAUDE.md`, or a
`.claude/commands/*.md` fix. Nothing here automates that; it's a deliberate
trade for not having to manage git branches across unrelated repos.

## What this deliberately leaves out

- **Provenance/confidence grading** (idea → active → checked → superseded,
  low/medium/high confidence, etc.) was in the original template this is
  based on and is intentionally dropped here — it added upkeep the workspace
  didn't clearly pay for. If you later want it back, add the fields to
  `investigations/INVESTIGATION_TEMPLATE.md` and the index tables; nothing
  else in this scaffold depends on their absence.
- **Enforcement of anything other than file-edit location.** The hook checks
  *which file* is being edited, not *what* was written to it — it can't catch
  a fabricated citation or a sign error. That's still your job, and the
  criticism phase's job.
- **Any imposed structure inside `ai/code_dev/` or `code/`.** Both are
  intentionally empty of scaffolding — whatever layout the project needs.
