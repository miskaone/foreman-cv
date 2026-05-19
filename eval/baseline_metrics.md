# Baseline Metrics

## Run

- Dataset: `mikes-workspace-3onpi/construction-site-safety-djmru` v1
- Model: `construction-site-safety-djmru/1` (RF-DETR Small, trained 2026-05-19)
- Roboflow report URL: https://app.roboflow.com/mikes-workspace-3onpi/construction-site-safety-djmru/1
- Training report image: [`roboflow_training_report.png`](./roboflow_training_report.png)
- Preprocessing: Resize 640x640 (Stretch to); no augmentation configured
- Augmentation: none

## Summary

| Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| --- | ---: | ---: | ---: | ---: |
| validation | 71.9% | 54.4% | 61.2% | 45.7% |
| test set | 74.5% | 61.0% | 65.2% | 47.0% |

## Per-class metrics

### Validation

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| --- | ---: | ---: | ---: | ---: |
| Excavator | 88.9% | 66.7% | 73.4% | 66.1% |
| Gloves | 86.7% | 52.0% | 59.5% | 36.8% |
| Hardhat | 94.2% | 82.3% | 87.0% | 64.4% |
| Ladder | 66.7% | 80.0% | 72.7% | 65.3% |
| Mask | 94.7% | 85.7% | 85.1% | 63.1% |
| NO-Hardhat | 80.0% | 63.8% | 64.9% | 33.5% |
| NO-Mask | 68.5% | 50.0% | 52.7% | 15.4% |
| NO-Safety Vest | 87.2% | 70.8% | 77.2% | 47.6% |
| Person | 87.1% | 81.3% | 87.2% | 68.6% |
| Safety Cone | 94.9% | 84.1% | 85.9% | 52.0% |
| Safety Vest | 93.8% | 73.2% | 85.1% | 59.8% |
| dump truck | 61.5% | 61.5% | 77.5% | 66.3% |
| machinery | 80.0% | 50.0% | 51.5% | 43.3% |
| mini-van | 0.0% | 0.0% | 16.7% | 11.7% |
| sedan | 0.0% | 0.0% | 17.9% | 9.8% |
| trailer | 100.0% | 100.0% | 100.0% | 100.0% |
| truck | 100.0% | 25.0% | 27.7% | 27.5% |
| truck and trailer | 0.0% | 0.0% | 6.6% | 2.8% |
| van | 100.0% | 33.3% | 46.9% | 36.3% |
| vehicle | 45.5% | 27.8% | 38.1% | 29.1% |
| wheel loader | 80.0% | 54.5% | 72.2% | 60.9% |
| all | 71.9% | 54.4% | 61.2% | 45.7% |

### Test

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| --- | ---: | ---: | ---: | ---: |
| Excavator | 77.8% | 77.8% | 85.9% | 77.5% |
| Gloves | 88.0% | 55.0% | 61.3% | 27.2% |
| Hardhat | 96.0% | 86.4% | 92.9% | 59.7% |
| Ladder | 66.7% | 80.0% | 81.3% | 71.7% |
| Mask | 80.8% | 75.0% | 74.8% | 50.8% |
| NO-Hardhat | 68.6% | 58.5% | 55.5% | 30.4% |
| NO-Mask | 76.4% | 69.6% | 64.5% | 21.6% |
| NO-Safety Vest | 86.8% | 73.3% | 75.0% | 47.8% |
| Person | 90.4% | 81.0% | 87.9% | 68.4% |
| Safety Cone | 65.1% | 44.6% | 45.7% | 19.0% |
| Safety Vest | 83.9% | 77.0% | 80.9% | 51.7% |
| dump truck | 100.0% | 75.0% | 87.9% | 82.8% |
| machinery | 100.0% | 33.3% | 49.5% | 41.6% |
| sedan | 0.0% | 0.0% | 1.2% | 0.1% |
| trailer | 100.0% | 100.0% | 100.0% | 90.0% |
| truck | 33.3% | 50.0% | 45.0% | 30.6% |
| van | 50.0% | 14.3% | 20.4% | 12.5% |
| vehicle | 76.9% | 33.3% | 45.4% | 39.6% |
| wheel loader | 75.0% | 75.0% | 83.3% | 69.1% |
| all | 74.5% | 61.0% | 65.2% | 47.0% |

## Sample predictions

- Best: [`sample_predictions/best.jpg`](./sample_predictions/best.jpg) — Clean single-worker PPE frame; model finds Person, Safety Vest, Hardhat, and Mask with high confidence.
- Worst: [`sample_predictions/worst.jpg`](./sample_predictions/worst.jpg) — Violation frame; model detects person/cones but classifies the vest/hardhat region as compliant Safety Vest/Hardhat while ground truth includes NO-Safety Vest and NO-Hardhat.

Both sample frames use burned-in prediction overlays generated from hosted Roboflow inference at confidence 0.25 / IoU 0.5.
