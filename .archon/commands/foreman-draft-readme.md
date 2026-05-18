---
description: Draft or revise the Foreman README as a Solutions Architect narrative artifact
argument-hint: <optional section or revision focus>
---

# Draft Foreman README

User request: $ARGUMENTS
Workflow artifacts: $ARTIFACTS_DIR

## Context

Foreman is a Roboflow-native rebuild of a master's capstone (hard-hat / PPE detection),
packaged as a Solutions Architect application artifact for Roboflow. The product framing
is **"the AI foreman that walks the site, watches the workers, and calls out the
violations."** Keep that metaphor consistent.

The strategic causal chain (load-bearing — every README section should advance one link):

> Master's capstone proves CV credibility → Roboflow rebuild proves platform fluency →
> SA-shaped demo proves you already think like the role → application converts from
> "stretch" to "memorable"

## Inputs to read before drafting

Read these files from the repo root (skip silently if missing — note their absence in
the draft instead of fabricating numbers):

1. `roboflow-sa-capstone-rebuild-prd-v0.1.md` — source of truth for scope and phases
2. `CLAUDE.md` — repo conventions and the phase model
3. `eval/baseline_metrics.md` — Phase 1 mAP results (if present)
4. `workflow.json` — Phase 2 Roboflow Workflow definition (if present)
5. `deploy/hosted_inference.py` and `deploy/local_inference.py` — Phase 3 artifacts (if present)

## Required README sections

1. **Hook** — one-paragraph "the AI foreman" framing. Concrete, not corporate.
2. **What it does** — detection → filter → expression block → alert/dataset sinks.
   The expression block is the ML→business pivot; call that out explicitly.
3. **Results** — mAP@0.5, mAP@0.5:0.95, per-class P/R from `eval/baseline_metrics.md`.
   Include the "best frame" and "worst frame" from `eval/sample_predictions/`.
4. **Architecture** — one mermaid diagram showing: dataset → train → Workflow → two deploys.
5. **Deploy two ways** — hosted (`inference-sdk` → `serverless.roboflow.com`) and local
   (`inference server start`). Same `workflow.json`, different endpoints. Show the
   minimal client snippet for each. **Both clients read credentials from env vars
   injected by `op run --env-file=.env.op --`** (1Password CLI); document this in the
   README so a reviewer cloning the repo knows to install `op` and sign in before
   running `python deploy/*.py`. The 1Password reference file `.env.op` is committed
   to the repo and contains `op://Private/Roboflow/*` references, never raw secrets.
6. **Why this matters for the SA conversation** — alerting, active learning loop via the
   dataset sink, visualization. Frame each Workflow block as the customer question it answers.
7. **What I'd do next** — 3–5 bullets of honest follow-ups (not a roadmap, not a wishlist).

## Voice and constraints

- Solutions Architect tone: confident, specific, no hedge-padding.
- No emoji. No "leverage", no "robust", no "seamlessly".
- Numbers come from files, not from memory. If a number isn't in a file, write
  `<TODO: read from eval/baseline_metrics.md>` instead of guessing.
- Keep the foreman metaphor — but don't belabor it. One vivid sentence at the top, then
  let the artifacts do the work.

## Output

Write the draft to `$ARTIFACTS_DIR/README.draft.md`. Do NOT overwrite the repo's
`README.md` — the user reviews and promotes the draft manually.

Report a short diff summary: which sections are complete, which have TODOs, and what
files are still missing for a clean Phase 4 ship.
