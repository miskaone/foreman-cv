# Foreman Dev Journal

Append-only log of issue-by-issue learnings. Three canonical hashtag tags applied to bullets:

- `#surprise` — an unexpected finding (a tool behaved differently than expected, a metric came in well outside the prior, etc.)
- `#dead-end` — something tried that didn't work, and the reason
- `#mental-model` — a framing shift that changed the approach

The Phase 4 LinkedIn writeup will harvest this file by tag. Sparse notes are fine; verbose ones get truncated. One entry per Linear issue, appended on PR merge (by the ship workflow's `journal-entry` node, or manually until that workflow is exercised end-to-end).

Newest entries at the top.

---

## 2026-05-20 — MIS-1182 — Configure a shared active-learning dataset sink for violation-positive examples

**What I built:** Declared the canonical shared active-learning sink target for violation-positive examples using `foreman-violation-active-learning` as the stable Roboflow project slug. The validator now fails fast when that target is missing or duplicated while keeping routing, dedupe semantics, per-class sinks, notification sinks, and dataset version pinning out of this slice.

**Test result:** Pass. `python3 -m json.tool eval/roboflow_workflow_mis_1172.json`, `python3 -m py_compile scripts/validate_roboflow_workflow_contract.py`, `python3 scripts/validate_roboflow_workflow_contract.py`, and `git diff --check` all passed. The ship workflow `run-tests` node skipped because no `TEST_COMMAND` is configured.

**Notes:**
- The ship worktree's `git diff main...HEAD` was empty even though the implementation branch had the committed MIS-1182 contract diff at `e5159d1`.  #surprise
- Without `TEST_COMMAND`, the ship node can only record a skipped automated test pass-through, so the meaningful evidence remains in the implementation summary's validator checks.  #dead-end
- The active-learning work split cleanly into a target contract first, with event routing and human-readable path documentation deferred to sibling issues.  #mental-model

**PR:** [#10](https://github.com/miskaone/foreman-cv/pull/10) (pending review/merge)

---

## 2026-05-20 — MIS-1173 — Wire violation count and expression block for violations greater than zero

**What I built:** Added the violation-count and expression contract on top of the filtered `ppe_violations` branch, exposing `violations` and `has_violations` as stable workflow outputs. The validator now locks the count source, the `violations > 0` expression, and deterministic zero/compliant/positive sample cases.

**Test result:** Pass. `python3 -m json.tool eval/roboflow_workflow_mis_1172.json`, `python3 -m py_compile scripts/validate_roboflow_workflow_contract.py`, `python3 scripts/validate_roboflow_workflow_contract.py`, and `git diff --check` all passed. The ship workflow `run-tests` node skipped because no `TEST_COMMAND` is configured.

**Notes:**
- `git diff main...HEAD` was empty in the ship worktree even though the implementation summary and implementation worktree showed the MIS-1173 contract changes.  #surprise
- The run-tests node had no `TEST_COMMAND`, so it could only skip automated testing while the implementation summary carried the validator evidence.  #dead-end
- The business pivot is a scalar contract: count filtered noncompliance detections first, then let the expression read only `violations > 0`.  #mental-model

**PR:** [#9](https://github.com/miskaone/foreman-cv/pull/9) (squash-merged as `e52a545`)

---

## 2026-05-20 — MIS-1179 — Add the PPE violation filter branch for NO-Hardhat, NO-Safety Vest, and NO-Mask

**What I built:** Added the `ppe_violation_filter` branch to the Roboflow workflow contract so raw detector predictions are filtered to exactly `NO-Hardhat`, `NO-Safety Vest`, and `NO-Mask`, then exposed as `ppe_violations`. The validator now locks that contract while continuing to reject downstream count, expression, sink, and person-correlation scope.

**Test result:** Pass. `python3 -m json.tool eval/roboflow_workflow_mis_1172.json`, `python3 -m py_compile scripts/validate_roboflow_workflow_contract.py`, `python3 scripts/validate_roboflow_workflow_contract.py`, and `git diff --check` all passed. The ship workflow `run-tests` node skipped because no `TEST_COMMAND` is configured.

**Notes:**
- `git diff main...HEAD` was empty even though the implementation summary showed the contract change surface, so the ship workflow can lose sight of work that has not reached the committed range.  #surprise
- The run-tests node had no `TEST_COMMAND`, so automated ship-time testing could only record a skip while relying on the implementation summary's validator evidence.  #dead-end
- The PPE filter is a pure class-allowlist branch over raw predictions, not the place for counts, gates, sinks, normalization, or person association.  #mental-model

**PR:** [#8](https://github.com/miskaone/foreman-cv/pull/8) (squash-merged as `82696de`)

---

## 2026-05-20 — MIS-1178 — Preserve the all-detections workflow path for visualization and metadata

**What I built:** Exposed `all_detections` as a stable raw workflow contract alias for `$steps.p1_object_detection.predictions` while preserving the existing `p1_object_detection_predictions` output. The validator now locks that contract and rejects violation-counting or sink-style scope creep for this slice.

**Test result:** Pass. `python3 -m json.tool eval/roboflow_workflow_mis_1172.json`, `python3 -m py_compile scripts/validate_roboflow_workflow_contract.py`, `python3 scripts/validate_roboflow_workflow_contract.py`, and `git diff --check` all passed.

**Notes:**
- `git diff main...HEAD` was empty even though the implementation summary identified the contract change surface, so ship-time diff checks can miss work that was not present in the committed range.  #surprise
- Generic repo test discovery did not find a test suite for this narrow artifact, so the contract validator became the meaningful verification path.  #dead-end
- `all_detections` is a downstream availability contract, not a transformation or alerting branch, which keeps visualization/metadata work decoupled from violation logic.  #mental-model

**PR:** [#6](https://github.com/miskaone/foreman-cv/pull/6) (squash-merged as `e8a62c2`)

---

## 2026-05-19 — MIS-1177 — Create the named Roboflow detection block using construction-site-safety-djmru/1

**What I built:** Created the Roboflow Workflow contract for the P2 detection block, exported `eval/roboflow_workflow_mis_1172.json`, and added `scripts/validate_roboflow_workflow_contract.py` to lock the expected model, block name, output name, output type, and selector.

**Test result:** Complete. The validator passed with `roboflow workflow contract ok`, CodeRabbit passed on PR #5, and the PR merged as `8498f46` after the review thread was outdated by the hardening patch.

**Notes:**
- CodeRabbit caught that selector-only output validation could allow a workflow with the right path but the wrong output identity to pass.  #surprise
- The first PR pass validated the output selector but not its `name` or `type`; downstream slices need all three fields stable.  #dead-end
- Treat the committed workflow export plus validator as the contract boundary for the next Roboflow Workflow slices, not just as a snapshot.  #mental-model

**PR:** [#5](https://github.com/miskaone/foreman-cv/pull/5) (squash-merged as `8498f46`)

## 2026-05-19 — MIS-1158 — Commit eval/baseline_metrics.md + sample_predictions

**What I built:** Generated Roboflow dataset version `construction-site-safety-djmru/1`, trained RF-DETR Small, and committed the Phase 1 baseline eval artifacts: `eval/baseline_metrics.md`, `eval/roboflow_training_report.png`, `eval/sample_predictions/best.jpg`, `eval/sample_predictions/worst.jpg`, and `eval/roboflow_training_results.json`.

**Test result:** Complete. Roboflow training finished successfully with validation mAP@0.5 **61.2%**, validation mAP@0.5:0.95 **45.7%**, test mAP@0.5 **65.2%**, and test mAP@0.5:0.95 **47.0%**. The Archon implement workflow reran on Codex/GPT-5.5 using the preflight dispatch plan and completed with all three tasks done and zero pending.

**Notes:**
- Roboflow MCP had enough access to generate the version and start/monitor training, even though the local 1Password Roboflow item did not expose a usable API key.  #surprise
- `versions_generate` required the resize payload key `format: "Stretch to"`; using `method` failed with `resize format "undefined" is invalid`.  #dead-end
- Archon implement requires the exact preflight `dispatch-plan.json` path as `$ARGUMENTS`; running it without that path fails at `read-dispatch-plan`.  #mental-model
- Archon worktrees only see committed source state, so eval artifacts had to be committed before the isolated implement rerun could verify them.  #mental-model
- Pillow was installed for the wrong architecture under the default Python; `arch -arm64 python3` was the working local image-rendering path.  #dead-end

**PR:** [#4](https://github.com/miskaone/foreman-cv/pull/4) (pending squash merge)

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
