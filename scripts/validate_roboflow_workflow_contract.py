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
EXPECTED_VIOLATION_COUNT_BLOCK = "ppe_violation_count"
EXPECTED_VIOLATION_EXPRESSION_BLOCK = "ppe_violation_expression"
EXPECTED_OUTPUT_NAME = "p1_object_detection_predictions"
EXPECTED_ALL_DETECTIONS_OUTPUT_NAME = "all_detections"
EXPECTED_VIOLATIONS_OUTPUT_NAME = "ppe_violations"
EXPECTED_VIOLATION_COUNT_OUTPUT_NAME = "violations"
EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME = "has_violations"
EXPECTED_OUTPUT_TYPE = "JsonField"
EXPECTED_VIOLATION_CLASSES = ("NO-Hardhat", "NO-Safety Vest", "NO-Mask")
EXPECTED_ACTIVE_LEARNING_SINK = {
    "name": "shared_violation_positive_examples",
    "workspace_slug": "mikes-workspace-3onpi",
    "project_slug": "foreman-violation-active-learning",
    "target": "mikes-workspace-3onpi/foreman-violation-active-learning",
    "provisioning": "pre_provisioned",
    "source_output": EXPECTED_VIOLATIONS_OUTPUT_NAME,
    "positive_gate_output": EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME,
    "scope": "violation-positive examples only",
}
ALLOWED_ACTIVE_LEARNING_SINK_KEYS = set(EXPECTED_ACTIVE_LEARNING_SINK)
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
ALLOWED_DEFERRED_STEP_NAMES = {
    EXPECTED_DETECTION_BLOCK,
    EXPECTED_VIOLATION_FILTER_BLOCK,
    EXPECTED_VIOLATION_COUNT_BLOCK,
    EXPECTED_VIOLATION_EXPRESSION_BLOCK,
}
ZERO_VIOLATION_SAMPLE = []
COMPLIANT_ONLY_SAMPLE = [
    {"class_name": "Person"},
    {"class_name": "Hardhat"},
    {"class_name": "Safety Vest"},
    {"class_name": "Mask"},
]
POSITIVE_NONCOMPLIANCE_SAMPLE = [
    {"class_name": "Person"},
    {"class_name": "NO-Hardhat"},
    {"class_name": "Safety Vest"},
    {"class_name": "NO-Safety Vest"},
    {"class_name": "NO-Mask"},
]


def validate_active_learning_sink(contract: dict[str, object]) -> bool:
    sinks = contract.get("active_learning_sinks")
    if not isinstance(sinks, list):
        print("missing active_learning_sinks list", file=sys.stderr)
        return False
    if len(sinks) != 1:
        print(f"expected exactly one active learning sink target, found {len(sinks)}", file=sys.stderr)
        return False

    sink = sinks[0]
    if not isinstance(sink, dict):
        print(f"unexpected active learning sink shape: {sink!r}", file=sys.stderr)
        return False
    extra_keys = set(sink) - ALLOWED_ACTIVE_LEARNING_SINK_KEYS
    missing_keys = ALLOWED_ACTIVE_LEARNING_SINK_KEYS - set(sink)
    if extra_keys or missing_keys:
        print(
            "unexpected active learning sink keys: "
            f"extra={sorted(extra_keys)!r}, missing={sorted(missing_keys)!r}",
            file=sys.stderr,
        )
        return False
    if sink != EXPECTED_ACTIVE_LEARNING_SINK:
        print(f"unexpected active learning sink target: {sink!r}", file=sys.stderr)
        return False
    if "/" in str(sink.get("project_slug")):
        print(f"project_slug must not include workspace or version: {sink.get('project_slug')!r}", file=sys.stderr)
        return False
    if "/" in str(sink.get("workspace_slug")):
        print(f"workspace_slug must not include project or version: {sink.get('workspace_slug')!r}", file=sys.stderr)
        return False
    target_parts = str(sink.get("target")).split("/")
    if target_parts != [sink.get("workspace_slug"), sink.get("project_slug")]:
        print(f"target must be workspace_slug/project_slug only: {sink.get('target')!r}", file=sys.stderr)
        return False
    return True


def has_forbidden_step_marker(value: object) -> bool:
    normalized = str(value or "").lower()
    parts = {part for part in re.split(r"[^a-z0-9]+", normalized) if part}
    return normalized in FORBIDDEN_STEP_EXACT_NAMES or bool(parts & FORBIDDEN_STEP_TERMS)


def get_one_step(steps: list[dict[str, object]], name: str) -> dict[str, object] | None:
    matches = [step for step in steps if step.get("name") == name]
    if len(matches) != 1:
        print(f"expected exactly one {name!r} step, found {len(matches)}", file=sys.stderr)
        return None
    return matches[0]


def detections_count_contract_result(detections: list[dict[str, object]]) -> tuple[int, bool]:
    ppe_violations = [
        detection
        for detection in detections
        if detection.get("class_name") in EXPECTED_VIOLATION_CLASSES
    ]
    violations = len(ppe_violations)
    return violations, violations > 0


def validate_sample_cases() -> bool:
    expected_cases = [
        ("zero ppe_violations", ZERO_VIOLATION_SAMPLE, 0, False),
        ("compliant-only detections", COMPLIANT_ONLY_SAMPLE, 0, False),
        ("positive noncompliance detections", POSITIVE_NONCOMPLIANCE_SAMPLE, 3, True),
    ]
    for name, detections, expected_violations, expected_has_violations in expected_cases:
        violations, has_violations = detections_count_contract_result(detections)
        if violations != expected_violations or has_violations != expected_has_violations:
            print(
                f"unexpected sample result for {name}: "
                f"violations={violations!r}, has_violations={has_violations!r}",
                file=sys.stderr,
            )
            return False
    return True


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text())
    if not validate_active_learning_sink(contract):
        return 1

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
    expected_stable_contract_names = {
        "violation_count": EXPECTED_VIOLATION_COUNT_BLOCK,
        "violation_expression": EXPECTED_VIOLATION_EXPRESSION_BLOCK,
        "violations": EXPECTED_VIOLATION_COUNT_OUTPUT_NAME,
        "has_violations": EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME,
    }
    for key, expected_value in expected_stable_contract_names.items():
        if stable_contract_names.get(key) != expected_value:
            print(
                f"unexpected stable_contract_names.{key}: "
                f"{stable_contract_names.get(key)!r}",
                file=sys.stderr,
            )
            return 1

    steps = spec.get("steps", [])
    selector = f"$steps.{EXPECTED_DETECTION_BLOCK}.predictions"
    detection = get_one_step(steps, EXPECTED_DETECTION_BLOCK)
    violation_filter = get_one_step(steps, EXPECTED_VIOLATION_FILTER_BLOCK)
    violation_count = get_one_step(steps, EXPECTED_VIOLATION_COUNT_BLOCK)
    violation_expression = get_one_step(steps, EXPECTED_VIOLATION_EXPRESSION_BLOCK)
    if not all((detection, violation_filter, violation_count, violation_expression)):
        return 1

    forbidden_steps = [
        step
        for step in steps
        if step.get("name") not in ALLOWED_DEFERRED_STEP_NAMES
        if any(has_forbidden_step_marker(step.get(field)) for field in ("name", "type"))
    ]
    if forbidden_steps:
        names = ", ".join(str(step.get("name", "<unnamed>")) for step in forbidden_steps)
        print(f"unexpected deferred workflow step(s): {names}", file=sys.stderr)
        return 1

    if detection.get("type") != "roboflow_core/roboflow_object_detection_model@v3":
        print(f"unexpected detection block type: {detection.get('type')!r}", file=sys.stderr)
        return 1
    if detection.get("model_id") != EXPECTED_MODEL_ID:
        print(f"unexpected model_id: {detection.get('model_id')!r}", file=sys.stderr)
        return 1
    if detection.get("images") != "$inputs.image":
        print(f"unexpected image input reference: {detection.get('images')!r}", file=sys.stderr)
        return 1

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

    if violation_count.get("type") != "roboflow_core/property_definition@v1":
        print(f"unexpected violation count type: {violation_count.get('type')!r}", file=sys.stderr)
        return 1
    violation_selector = f"$steps.{EXPECTED_VIOLATION_FILTER_BLOCK}.predictions"
    if violation_count.get("data") != violation_selector:
        print(f"unexpected violation count source: {violation_count.get('data')!r}", file=sys.stderr)
        return 1
    expected_count_operations = [
        {
            "type": "DetectionsPropertyExtract",
            "property_name": "count",
        }
    ]
    if violation_count.get("operations") != expected_count_operations:
        print("unexpected violation count operations", file=sys.stderr)
        return 1

    if violation_expression.get("type") != "roboflow_core/expression@v1":
        print(f"unexpected violation expression type: {violation_expression.get('type')!r}", file=sys.stderr)
        return 1
    if violation_expression.get("data") != {
        "violations": f"$steps.{EXPECTED_VIOLATION_COUNT_BLOCK}.output"
    }:
        print(f"unexpected violation expression data: {violation_expression.get('data')!r}", file=sys.stderr)
        return 1
    expected_expression_switch = {
        "type": "CasesDefinition",
        "cases": [
            {
                "type": "CaseDefinition",
                "condition": {
                    "type": "StatementGroup",
                    "statements": [
                        {
                            "type": "BinaryStatement",
                            "left_operand": {
                                "type": "DynamicOperand",
                                "operand_name": "violations",
                            },
                            "comparator": {"type": ">"},
                            "right_operand": {
                                "type": "StaticOperand",
                                "value": 0,
                            },
                        }
                    ],
                },
                "result": {
                    "type": "StaticCaseResult",
                    "value": True,
                },
            }
        ],
        "default": {
            "type": "StaticCaseResult",
            "value": False,
        },
    }
    if violation_expression.get("switch") != expected_expression_switch:
        print("unexpected violation expression switch", file=sys.stderr)
        return 1

    outputs = spec.get("outputs", [])
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

    count_output_names = [
        output for output in outputs if output.get("name") == EXPECTED_VIOLATION_COUNT_OUTPUT_NAME
    ]
    if len(count_output_names) != 1:
        print(
            f"expected exactly one output named {EXPECTED_VIOLATION_COUNT_OUTPUT_NAME!r}, "
            f"found {len(count_output_names)}",
            file=sys.stderr,
        )
        return 1
    count_outputs = [
        output
        for output in outputs
        if output.get("name") == EXPECTED_VIOLATION_COUNT_OUTPUT_NAME
        and output.get("type") == EXPECTED_OUTPUT_TYPE
        and output.get("selector") == f"$steps.{EXPECTED_VIOLATION_COUNT_BLOCK}.output"
    ]
    if len(count_outputs) != 1:
        print(
            "missing expected violation count output contract: "
            f"(name={EXPECTED_VIOLATION_COUNT_OUTPUT_NAME!r}, type={EXPECTED_OUTPUT_TYPE!r}, "
            f"selector='$steps.{EXPECTED_VIOLATION_COUNT_BLOCK}.output')",
            file=sys.stderr,
        )
        return 1

    expression_output_names = [
        output for output in outputs if output.get("name") == EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME
    ]
    if len(expression_output_names) != 1:
        print(
            f"expected exactly one output named {EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME!r}, "
            f"found {len(expression_output_names)}",
            file=sys.stderr,
        )
        return 1
    expression_outputs = [
        output
        for output in outputs
        if output.get("name") == EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME
        and output.get("type") == EXPECTED_OUTPUT_TYPE
        and output.get("selector") == f"$steps.{EXPECTED_VIOLATION_EXPRESSION_BLOCK}.output"
    ]
    if len(expression_outputs) != 1:
        print(
            "missing expected violation expression output contract: "
            f"(name={EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME!r}, type={EXPECTED_OUTPUT_TYPE!r}, "
            f"selector='$steps.{EXPECTED_VIOLATION_EXPRESSION_BLOCK}.output')",
            file=sys.stderr,
        )
        return 1

    if not validate_sample_cases():
        return 1

    print("roboflow workflow contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
