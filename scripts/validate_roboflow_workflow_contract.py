#!/usr/bin/env python3
"""Validate Foreman's committed Roboflow workflow contract artifact."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONTRACT_PATH = Path("eval/roboflow_workflow_mis_1172.json")
EXPECTED_MODEL_ID = "construction-site-safety-djmru/1"
EXPECTED_DETECTION_BLOCK = "p1_object_detection"
EXPECTED_VIOLATION_FILTER_BLOCK = "ppe_violation_filter"
EXPECTED_OUTPUT_NAME = "p1_object_detection_predictions"
EXPECTED_ALL_DETECTIONS_OUTPUT_NAME = "all_detections"
EXPECTED_VIOLATIONS_OUTPUT_NAME = "ppe_violations"
EXPECTED_OUTPUT_TYPE = "JsonField"
EXPECTED_VIOLATION_CLASSES = ("NO-Hardhat", "NO-Safety Vest", "NO-Mask")
FORBIDDEN_STEP_EXACT_NAMES = {"dataset_sink"}
FORBIDDEN_STEP_TERMS = {
    "association",
    "correlation",
    "count",
    "email",
    "expression",
    "notification",
    "person",
    "sink",
    "slack",
    "visualization",
    "worker",
}


def has_forbidden_step_marker(value: object) -> bool:
    normalized = str(value or "").lower()
    parts = {part for part in re.split(r"[^a-z0-9]+", normalized) if part}
    return normalized in FORBIDDEN_STEP_EXACT_NAMES or bool(parts & FORBIDDEN_STEP_TERMS)


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text())
    spec = contract["specification"]
    stable_contract_names = contract.get("stable_contract_names", {})
    if stable_contract_names.get("detection_block") != EXPECTED_DETECTION_BLOCK:
        print(
            "unexpected stable_contract_names.detection_block: "
            f"{stable_contract_names.get('detection_block')!r}",
            file=sys.stderr,
        )
        return 1
    if stable_contract_names.get("all_detections") != EXPECTED_ALL_DETECTIONS_OUTPUT_NAME:
        print(
            "unexpected stable_contract_names.all_detections: "
            f"{stable_contract_names.get('all_detections')!r}",
            file=sys.stderr,
        )
        return 1
    if stable_contract_names.get("violation_filter") != EXPECTED_VIOLATION_FILTER_BLOCK:
        print(
            "unexpected stable_contract_names.violation_filter: "
            f"{stable_contract_names.get('violation_filter')!r}",
            file=sys.stderr,
        )
        return 1
    if stable_contract_names.get("violation_output") != EXPECTED_VIOLATIONS_OUTPUT_NAME:
        print(
            "unexpected stable_contract_names.violation_output: "
            f"{stable_contract_names.get('violation_output')!r}",
            file=sys.stderr,
        )
        return 1

    steps = spec.get("steps", [])
    selector = f"$steps.{EXPECTED_DETECTION_BLOCK}.predictions"
    matches = [step for step in steps if step.get("name") == EXPECTED_DETECTION_BLOCK]
    if len(matches) != 1:
        print(f"expected exactly one {EXPECTED_DETECTION_BLOCK!r} step, found {len(matches)}", file=sys.stderr)
        return 1

    violation_filter_matches = [
        step for step in steps if step.get("name") == EXPECTED_VIOLATION_FILTER_BLOCK
    ]
    if len(violation_filter_matches) != 1:
        print(
            f"expected exactly one {EXPECTED_VIOLATION_FILTER_BLOCK!r} step, "
            f"found {len(violation_filter_matches)}",
            file=sys.stderr,
        )
        return 1

    forbidden_steps = [
        step
        for step in steps
        if any(has_forbidden_step_marker(step.get(field)) for field in ("name", "type"))
    ]
    if forbidden_steps:
        names = ", ".join(str(step.get("name", "<unnamed>")) for step in forbidden_steps)
        print(f"unexpected deferred workflow step(s): {names}", file=sys.stderr)
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

    violation_filter = violation_filter_matches[0]
    if violation_filter.get("type") != "roboflow_core/detections_filter@v1":
        print(f"unexpected violation filter type: {violation_filter.get('type')!r}", file=sys.stderr)
        return 1
    if violation_filter.get("predictions") != selector:
        print(f"unexpected violation filter source: {violation_filter.get('predictions')!r}", file=sys.stderr)
        return 1

    expected_operations = [
        {
            "type": "DetectionsFilter",
            "filter_operation": {
                "type": "StatementGroup",
                "statements": [
                    {
                        "type": "BinaryStatement",
                        "left_operand": {
                            "type": "DynamicOperand",
                            "operations": [
                                {
                                    "type": "ExtractDetectionProperty",
                                    "property_name": "class_name",
                                }
                            ],
                        },
                        "comparator": {"type": "in (Sequence)"},
                        "right_operand": {
                            "type": "DynamicOperand",
                            "operand_name": "classes",
                        },
                    }
                ],
            },
        }
    ]
    if violation_filter.get("operations") != expected_operations:
        print("unexpected violation filter operations", file=sys.stderr)
        return 1

    classes = violation_filter.get("operations_parameters", {}).get("classes")
    if classes != list(EXPECTED_VIOLATION_CLASSES):
        print(f"unexpected violation class allowlist: {classes!r}", file=sys.stderr)
        return 1

    outputs = spec.get("outputs", [])
    violation_selector = f"$steps.{EXPECTED_VIOLATION_FILTER_BLOCK}.predictions"
    expected_outputs = {
        EXPECTED_OUTPUT_NAME,
        EXPECTED_ALL_DETECTIONS_OUTPUT_NAME,
    }
    matching_output_names = {
        output.get("name")
        for output in outputs
        if output.get("selector") == selector and output.get("type") == EXPECTED_OUTPUT_TYPE
    }
    missing_outputs = expected_outputs - matching_output_names
    if missing_outputs:
        print(
            "missing expected output contract(s): "
            + ", ".join(
                f"(name={name!r}, type={EXPECTED_OUTPUT_TYPE!r}, selector={selector!r})"
                for name in sorted(missing_outputs)
            ),
            file=sys.stderr,
        )
        return 1

    violation_outputs = [
        output
        for output in outputs
        if output.get("name") == EXPECTED_VIOLATIONS_OUTPUT_NAME
        and output.get("type") == EXPECTED_OUTPUT_TYPE
        and output.get("selector") == violation_selector
    ]
    if len(violation_outputs) != 1:
        print(
            "missing expected violation output contract: "
            f"(name={EXPECTED_VIOLATIONS_OUTPUT_NAME!r}, type={EXPECTED_OUTPUT_TYPE!r}, "
            f"selector={violation_selector!r})",
            file=sys.stderr,
        )
        return 1

    print("roboflow workflow contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
