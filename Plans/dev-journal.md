# Foreman Dev Journal

Append-only log of issue-by-issue learnings. Three canonical hashtag tags applied to bullets:

- `#surprise` — an unexpected finding (a tool behaved differently than expected, a metric came in well outside the prior, etc.)
- `#dead-end` — something tried that didn't work, and the reason
- `#mental-model` — a framing shift that changed the approach

The Phase 4 LinkedIn writeup will harvest this file by tag. Sparse notes are fine; verbose ones get truncated. One entry per Linear issue, appended on PR merge (by the ship workflow's `journal-entry` node, or manually until that workflow is exercised end-to-end).

Newest entries at the top.

---

## 2026-05-19 — MIS-1158 — Commit eval/baseline_metrics.md + sample_predictions

**What I built:** Generated Roboflow dataset version `construction-site-safety-djmru/1`, trained RF-DETR Small, and committed the Phase 1 baseline eval artifacts: `eval/baseline_metrics.md`, `eval/roboflow_training_report.png`, `eval/sample_predictions/best.jpg`, `eval/sample_predictions/worst.jpg`, and `eval/roboflow_training_results.json`.

**Test result:** Complete. Roboflow training finished successfully with validation mAP@0.5 **61.2%**, validation mAP@0.5:0.95 **45.7%**, test mAP@0.5 **65.2%**, and test mAP@0.5:0.95 **47.0%**. The Archon implement workflow reran on Codex/GPT-5.5 using the preflight dispatch plan and completed with all three tasks done and zero pending.

**Notes:**
- Roboflow MCP had enough access to generate the version and start/monitor training, even though the local 1Password Roboflow item did not expose a usable API key.  #surprise
- `versions_generate` required the resize payload key `format: "Stretch to"`; using `method` failed with `resize format "undefined" is invalid`.  #dead-end
- Archon implement requires the exact preflight `dispatch-plan.json` path as `$ARGUMENTS`; running it without that path fails at `read-dispatch-plan`.  #mental-model
- Archon worktrees only see committed source state, so eval artifacts had to be committed before the isolated implement rerun could verify them.  #mental-model
- Pillow was installed for the wrong architecture under the default Python; `arch -arm64 python3` was the working local image-rendering path.  #dead-end

**Commit:** `d8e0d6c` (`Publish Roboflow baseline evaluation artifacts`)

## 2026-05-18 — MIS-1168 — Build the three foreman dev workflow Archon YAMLs

**What I built:** Three chained vendor-agnostic Archon workflows (`preflight`, `implement`, `ship`) for the per-issue dev cycle, plus the `.env.op` plumbing for 1Password credential injection. All three pass `archon validate workflows`; discovery count went from 21 → 24.

**Test result:** Partial. Structural validation, `op run` credential resolution, `fetch-issue` (Linear API), and the first `grill-limited` AI iteration all worked end-to-end on a live invocation against MIS-1158. Full chain to `dispatch-plan.json` was deferred — `archon workflow run` exits when the workflow pauses for approval, and there's no persistent runner picking up the queued approval to resume. Resolved by either running `archon serve` in another terminal or finding the right `--resume` invocation — not a workflow YAML bug.

**Notes:**
- The YAML literal block scalar `|` silently terminates when an inner line drops below the block's column indent — embedding a multi-line bash string with column-0 lines broke `archon validate`. `printf` to build the message is the portable fix.  #dead-end
- Vendor-agnostic workflows just *omit* `provider:` and `model:` — there's no explicit "agnostic mode," the runtime simply falls back to `.archon/config.yaml`. The absence pattern IS the agnostic pattern.  #mental-model
- `output_format` is reliable on both Claude and Codex per Archon's parameter matrix, so structured JSON decisions can survive a vendor swap without rewriting `when:` conditions.  #surprise
- The `${VAR:?error}` bash construct only checks env vars, not Archon's template-rendered substitutions — `$ARGUMENTS` gets substituted at template time but is *not* also set as a runtime env var. Direct substitution + explicit empty-string check is the portable pattern.  #dead-end
- 1Password CLI can't `op item edit` items containing `ssoLogin` fields (Google/Apple sign-in linkages) — created when Roboflow signup happened via "Continue with Google." Workaround: keep `.env.op` to credentials only; non-secret config lives in workflow YAML or code.  #dead-end
- The AI grilling node independently surfaced the same "best/worst frame selection" decision that came out of the human Grill-Me session four hours earlier — different paths, same identified decision. The decision-tree-first framing of the prompt was load-bearing.  #mental-model
- Archon's interactive workflows need a persistent runner (`archon serve` or attached foreground `--resume`) to consume queued approvals — `archon workflow run` exits when paused. Worth designing the runtime UX with this in mind.  #surprise
- GitHub branch protection with `required_approving_review_count: 0` still creates a "Reviews required" check that needs *some* review interaction — solo merges either need `--admin` (configured escape hatch) or a self-review submitted before merge. The cleaner long-term fix is the `archon-smart-pr-review` workflow producing review findings, then a real `gh pr review --approve` based on those findings.  #surprise

**PR:** [#1](https://github.com/miskaone/foreman-cv/pull/1) (squash-merged as `54832d1`)

---
