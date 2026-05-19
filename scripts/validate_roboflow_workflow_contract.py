#!/usr/bin/env python3
"""Validate Foreman's committed Roboflow workflow contract artifact."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_PATH = Path("eval/roboflow_workflow_mis_1172.json")
EXPECTED_MODEL_ID = "construction-site-safety-djmru/1"
EXPECTED_DETECTION_BLOCK = "p1_object_detection"
EXPECTED_OUTPUT_NAME = "p1_object_detection_predictions"
EXPECTED_OUTPUT_TYPE = "JsonField"


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text())
    spec = contract["specification"]
    steps = spec.get("steps", [])
    matches = [step for step in steps if step.get("name") == EXPECTED_DETECTION_BLOCK]
    if len(matches) != 1:
        print(f"expected exactly one {EXPECTED_DETECTION_BLOCK!r} step, found {len(matches)}", file=sys.stderr)
        return 1

    detection = matches[0]
    if detection.get("type") != "roboflow_core/roboflow_object_detection_model@v3":
        print(f"unexpected detection block type: {detection.get('type')!r}", file=sys.stderr)
        return 1
    if detection.get("model_id") != EXPECTED_MODEL_ID:
        print(f"unexpected model_id: {detection.get('model_id')!r}", file=sys.stderr)
        return 1
    if detection.get("images") != "$inputs.image":
        print(f"unexpected image input reference: {detection.get('images')!r}", file=sys.stderr)
        return 1

    outputs = spec.get("outputs", [])
    selector = f"$steps.{EXPECTED_DETECTION_BLOCK}.predictions"
    if not any(
        output.get("selector") == selector
        and output.get("name") == EXPECTED_OUTPUT_NAME
        and output.get("type") == EXPECTED_OUTPUT_TYPE
        for output in outputs
    ):
        print(
            "missing expected output contract "
            f"(name={EXPECTED_OUTPUT_NAME!r}, type={EXPECTED_OUTPUT_TYPE!r}, selector={selector!r})",
            file=sys.stderr,
        )
        return 1

    print("roboflow workflow contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
