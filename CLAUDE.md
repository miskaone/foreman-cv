# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repo is **PRD-stage**. The only artifact today is `roboflow-sa-capstone-rebuild-prd-v0.1.md` plus an empty `Plans/` directory. There is no source code, no package manifest, no test suite, no git history yet. Any "how do I run X" question for this repo currently has the same answer: the thing doesn't exist yet — read the PRD, find the phase it belongs to, and either build the missing piece or tell the user what's still missing.

## What Foreman is

**Foreman** is a Roboflow-native rebuild of a 2023 master's capstone (hard-hat / PPE detection), being packaged as a Solutions Architect application artifact for Roboflow (Ashby JID `fa06d985`). The product framing — "the AI foreman that walks the site, watches the workers, and calls out the violations" — is load-bearing across the repo, README, Loom, and LinkedIn post. Keep that metaphor consistent in any user-facing prose you generate.

The strategic causal chain the PRD is built on:

> Master's capstone proves CV credibility → Roboflow rebuild proves platform fluency → SA-shaped demo proves you already think like the role → application converts from "stretch" to "memorable"

If a proposed change doesn't advance one of those links, it's probably out of scope.

## Phase model (this is the architecture)

The PRD is structured as four sequential phases with a hard gate at P1. The phase determines what you should build:

- **Phase 1 — Train & validate** (Sat AM, 3–4h). Fork `roboflow-universe-projects/construction-site-safety` (717 imgs, 10 classes) into a Roboflow workspace, train **RF-DETR** (fallback: **YOLO11n** if free-tier queues stall), document baseline mAP in `eval/baseline_metrics.md`. **This is the ship gate.** If P1 doesn't land clean, drop to fallback before sinking time into P2+.
- **Phase 2 — Workflow build** (Sat PM, 2–3h). Build a Roboflow Workflow: detection → class filter → property/count blocks → expression block (`violations > 0`) → email/Slack sink + dataset sink + bounding-box viz. The expression block is the bridge from ML output to business outcome — that's the SA-narrative pivot, not a detail.
- **Phase 3 — Deploy two ways** (Sun AM, 1–2h). Hosted via `pip install inference-sdk` calling `https://serverless.roboflow.com`, and local via `pip install inference` running `inference server start`. Same `workflow.json`, different endpoints. Both files live under `deploy/`.
- **Phase 4 — Package & pitch** (Sun PM, 2–3h). README writeup, 3–5 min Loom, LinkedIn post (causal-hook format), Ashby application submission with links.

**Hard stop rule from the PRD:** if Phase 4 isn't done by Sun 6PM, ship P1+P2+LinkedIn and apply Monday with what exists. Partial public artifact beats polished private one.

## Expected future structure

The PRD specifies the target layout (§6.1) — when you create files, match these paths exactly:

```
foreman/
├── README.md                    # SA narrative writeup
├── workflow.json                # Exported Roboflow Workflow definition
├── deploy/
│   ├── hosted_inference.py      # serverless.roboflow.com client
│   └── local_inference.py       # local inference server client
├── eval/
│   ├── baseline_metrics.md      # P1 training output: mAP@0.5, mAP@0.5:0.95, per-class P/R
│   └── sample_predictions/      # one "best" frame, one "worst" frame
├── assets/                      # mermaid renders, architecture diagrams
└── LICENSE                      # MIT
```

The `Plans/` directory in the current tree is for PRD iteration (v0.2+, open questions in §9) — keep code out of it.

## Naming and slug

The product name is **Foreman** everywhere user-facing. The GitHub repo is **`miskaone/foreman-cv`** (resolved 2026-05-18, see PRD §9). The repo may not exist on GitHub yet — confirm with the user before running `gh repo create` or `git push`.

## Build / test commands

None defined yet. When P1 lands, the project will be Python-based (`inference-sdk`, `inference`). Until then, there is nothing to lint, build, or test in this repo — the work happens inside the Roboflow web app (dataset fork, training run, Workflow editor) and the artifacts (`workflow.json`, `deploy/*.py`, `eval/baseline_metrics.md`) get committed back here.

## Working style notes from the PRD

- **Use the canonical Roboflow dataset, not an obscure one.** The PRD explicitly chose `roboflow-universe-projects/construction-site-safety` because "customer-facing SAs don't pick obscure datasets when the official one exists." Don't substitute without re-reading §3.1.
- **RF-DETR over YOLO11n is intentional signal**, not a casual choice — the Roboflow careers page links to the RF-DETR blog post. Only fall back if queues actually stall.
- **The Workflow's purpose is the SA conversation**, not detection accuracy. Every block in §4.2 maps to a customer question (alerting, active learning, visualization). If you propose a Workflow change, frame it in those terms.
- **Phase 1 = ship signal.** If you can answer "my fine-tuned RF-DETR hits X mAP on the canonical construction-site dataset; here's a frame" in one sentence, Phase 1 is done. Anything after that is upside, not required.
