# Foreman P1 — Cheat Sheet

Pin this on the wall. Don't re-litigate these decisions under pressure.

---

## Pre-flight (already done — verify before starting)

- [ ] Roboflow workspace: `mikes-workspace-3onpi` (https://app.roboflow.com/mikes-workspace-3onpi)
- [ ] Dataset forked: `construction-site-safety-djmru` (717 imgs, 25 classes — *not 10 as PRD said*)
- [ ] `ROBOFLOW_API_KEY` in 1Password (`op://Private/Roboflow/credential`)
- [ ] `.env.op` exists at repo root
- [ ] Verify with: `op read 'op://Private/Roboflow/credential' | head -c 8` → should print `AJSP...`
- [ ] Credit budget: 15/month, 0.07 used. Resets May 31. Overage blocked by default.

---

## The 10 locked decisions

| Q | Decision | One-line reason |
|---|---|---|
| Q1 | Account exists (Mikes Workspace, Public Plan) | Done |
| Q2 | Train on all 25 classes, **report both 25-class and PPE-subset metrics** | Honesty + the PPE subset is what the SA narrative needs |
| Q3 | **RF-DETR Small** for both runs | Roboflow's default; best capacity-to-data ratio for 717 imgs |
| Q4 | **Run 1 version = no augmentation**, 640×640, auto-orient on, inherit upstream split | Clean baseline = honest interpretation later |
| Q5 | **Fallback A + D**: 30-min queue / 90-min total limit; always run **YOLO11n in parallel** as insurance | Protects budget; gives the cost-conscious-customer story |
| Q6 | **Two runs**: Run 1 defaults no-aug, Run 2 same model + Roboflow aug | Augmentation reliably moves mAP 5-15%; better than hyperparam tuning at this scale |
| Q7 | **Ship-gate D (compound)**: Hard gate = run completes + metrics file. Proud gate = PPE-subset mAP@0.5 ≥ 0.65 AND recall ≥ 0.5 on `NO-Hardhat` or `NO-Safety Vest` | Hard gate = PRD compliance; proud gate = business meaning |
| Q8 | **Construction-curated aug**: horizontal flip ON, vertical flip OFF, 90° rotate OFF, rotation ±15° ON, brightness/contrast/crop/shear/blur/noise ON at defaults, hue/saturation/grayscale OFF | Gravity exists; PPE colors are diagnostic |
| Q9 | **Best frame** = multi-class scene with mixed compliance, all detections correct. **Worst frame** = honest miss on a fair scene (occlusion, not impossible distance) | Best = SA pitch in one image; worst = honest failure mode that explains itself |
| Q10 | **`eval/baseline_metrics.md` layered**: TL;DR → dataset → config → results (full + PPE subset) → per-class → aug rationale → YOLO11n parallel → visual samples → failure analysis → what's next → reproducibility | Lets the README quote the TL;DR while preserving full data underneath |

---

## Saturday execution sequence

### 1. Generate Run 1 dataset version (Q4)
- Open the forked project → Generate New Version
- Preprocessing: Auto-orient ON, Resize 640×640
- **Augmentations: NONE**
- Train/val/test split: inherit upstream
- Click Generate. Expected output size ≈ 717 images.

### 2. Start Run 1 training (Q3 + Q6)
- Engine: Custom Training
- Model: RF-DETR Small
- Hyperparameters: defaults. Watch the epoch count — **if it shows >200 epochs with no early stopping, drop to 100**.
- Note the start time. **Q5 timer starts now.**

### 3. Start parallel YOLO11n training (Q5 Path D)
- Same Run 1 version, immediately fire YOLO11n.
- Insurance run. Cheap (~1 credit, ~15-25 min).

### 4. Q5 fallback timer rules
```
T+30 min   If RF-DETR still "pending" (queue not started)
           → note wait time, continue monitoring.

T+60 min   If RF-DETR still hasn't started
           → FALLBACK declared. Use YOLO11n run as baseline.

T+90 min   Hard ceiling on RF-DETR total time.
           Whichever finished first wins.
```

### 5. Inspect Run 1 results (Q6 discipline)
Before running Run 2, write a one-sentence hypothesis based on training curves:
- Train loss still descending at last epoch → underfit → consider +50 epochs
- Val mAP plateaus by epoch 30 → saturated → aug is the right next move (which we're already doing)
- Train mAP climbs while val descends → overfit, no aug → confirms aug as next move
- GPU OOM → halve batch size
- LR too high (val loss explodes mid-training) → halve LR

If none of these symptoms apply but mAP is below proud-gate: **augmentation is the play** (which is already Run 2). Don't tune hyperparameters.

### 6. Generate Run 2 dataset version (Q8 — construction-curated aug)
| Augmentation | Setting |
|---|---|
| Horizontal flip | ON |
| Vertical flip | **OFF** |
| 90° rotate | **OFF** |
| Rotation (±15°) | ON (default magnitude) |
| Brightness | ON (default) |
| Contrast | ON (default) |
| Crop / zoom | ON (default) |
| Shear | ON (small) |
| Blur | ON (slight) |
| Noise | ON (slight) |
| Hue shift | **OFF** |
| Saturation | **OFF** (or very slight) |
| Grayscale | **OFF** |

**Watch:** if the generated dataset size is >3× source (>2150 imgs), the aug pipeline is more aggressive than expected. Disable a few before clicking Generate.

### 7. Start Run 2 training
- Same model: RF-DETR Small
- Same hyperparameters: defaults (or whatever you settled on in Q6 hypothesis)
- Same Q5 timer rules apply (probably won't queue this time, fresh slot)

### 8. Run inference on test set
- Use the winning model (likely Run 2)
- Generate predictions on held-out test set with confidence + ground truth overlays

### 9. Select sample frames (Q9)
**Best — process:**
1. Filter test predictions to frames where ground truth contains BOTH a PPE-compliant class (Hardhat / Safety Vest) AND a violation class (NO-Hardhat / NO-Safety Vest / NO-Mask) in the same image.
2. Within that set, find frames where every ground-truth box was correctly predicted (IoU > 0.5, correct class).
3. Pick the visually clearest one.
4. Export: `eval/sample_predictions/best_mixed_compliance.png`

**Worst — process:**
1. Filter to frames where the model missed at least one violation-class ground truth.
2. Exclude extreme occlusion / unreasonable distance.
3. Pick one with an identifiable, namable failure cause.
4. Export: `eval/sample_predictions/worst_missed_violation.png`

Both PNGs: predicted boxes in green, ground truth in red.

### 10. Write `eval/baseline_metrics.md` (Q10)
Structure:
```
# Foreman — Baseline Metrics

## TL;DR
## Dataset
## Training config
## Results — overall (25 classes)
## Results — PPE-relevant subset (7 classes)
## Per-class P/R (Run 2, headline run)
## Augmentation rationale
## YOLO11n parallel run (insurance baseline)
## Visual samples
## Failure mode analysis
## What I'd improve next
## Reproducibility
```

### 11. Apply ship-gate (Q7)
**Hard gate** (always ship if met):
- [ ] A training run completed
- [ ] `eval/baseline_metrics.md` exists with mAP@0.5, mAP@0.5:0.95, per-class P/R
- [ ] Both sample frames in `eval/sample_predictions/`

**Proud gate** (changes README framing if missed):
- [ ] PPE-subset mAP@0.5 ≥ 0.65
- [ ] Recall ≥ 0.5 on `NO-Hardhat` OR `NO-Safety Vest`

If hard gate met but proud gate missed: ship as-is. README pivots — frame the baseline honestly, make "What I'd improve next" the strongest section. **Do NOT switch to the 22k-image fallback dataset.** Don't dataset-shop.

---

## Credit budget tracker

| Item | Estimated credits | Running total |
|---|---|---|
| Already used (dataset fork) | 0.07 | 0.07 |
| Run 1 RF-DETR Small (defaults, ~30-60 min) | 1-2 | ~1.07-2.07 |
| Run 1 parallel YOLO11n (~15-25 min) | ~1 | ~2.07-3.07 |
| Run 2 RF-DETR Small + aug (~30-60 min) | 1-2 | ~3.07-5.07 |
| Hard ceiling on per-run cost | abort if confirmation modal shows >6 credits/run | |
| **P1 reserve** | **~10-12 credits left of 15** | resets May 31 |

---

## What's *out of scope* for P1

- Don't switch datasets (22k-image fallback) — that's dataset-shopping, not engineering.
- Don't tune multiple hyperparameters at once.
- Don't add Run 3 / Run 4 without a written reason. The narrative is `baseline → with-aug`, not `here are six runs`.
- Don't rename the workspace slug (only the display name, and only if you want to).
- Don't start Phase 2 work until Phase 1's `eval/` artifacts are committed.

---

## Links

- Roboflow workspace: https://app.roboflow.com/mikes-workspace-3onpi
- Forked project: https://app.roboflow.com/mikes-workspace-3onpi/construction-site-safety-djmru
- Linear P1 milestone: see issues MIS-1156, MIS-1157, MIS-1158
- PRD: `roboflow-sa-capstone-rebuild-prd-v0.1.md`
- Credentials: `op://Private/Roboflow/*` resolved via `op run --env-file=.env.op --`
