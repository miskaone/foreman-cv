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
EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH = "post_expression_violation_positive"
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
    "source_output": EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH,
    "positive_gate_output": EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME,
    "scope": "violation-positive examples only",
    "record_contract": {
        "dedupe_key": {
            "name": "dedupe_key",
            "required": True,
            "derivation_stage": "before_class_expansion",
            "primary_identity": "upstream positive frame/source event identity",
            "preferred_source": "persisted event_id or frame_id when present",
            "fallback_source": (
                "stable composite of normalized source identity plus frame index, "
                "event timestamp or offset, and capture-window identity"
            ),
            "empty_value_allowed": False,
        },
        "collapse_strategy": {
            "key": "dedupe_key",
            "one_sink_example_per": "positive frame/source event",
            "duplicate_class_expanded_records": "collapse_to_one_visual_example",
            "preserve_metadata": [
                "noncompliance_classes",
                "noncompliance_reasons",
                "source_detections",
            ],
        },
        "record_scope": (
            "one positive frame/source event maps to one active-learning sink example, "
            "not one noncompliance class"
        ),
    },
}
ALLOWED_ACTIVE_LEARNING_SINK_KEYS = set(EXPECTED_ACTIVE_LEARNING_SINK)
EXPECTED_ALERT_SINK_STUBS = [
    {
        "name": "email_violation_alert_stub",
        "type": "email",
        "enabled": False,
        "environment": "test_only",
        "delivery_mode": "disabled",
        "sends_live_notifications": False,
        "gate_output": EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME,
        "source_output": EXPECTED_VIOLATIONS_OUTPUT_NAME,
        "placeholder_recipient": "foreman-alerts@example.invalid",
        "placeholder_subject": "[TEST ONLY] Foreman PPE violation alert",
        "notes": "Disabled non-production placeholder; replace before production handoff.",
    },
    {
        "name": "slack_violation_alert_stub",
        "type": "slack",
        "enabled": False,
        "environment": "test_only",
        "delivery_mode": "disabled",
        "sends_live_notifications": False,
        "gate_output": EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME,
        "source_output": EXPECTED_VIOLATIONS_OUTPUT_NAME,
        "placeholder_webhook_url": "https://example.invalid/slack/foreman-alerts-placeholder",
        "placeholder_channel": "#foreman-alerts-placeholder",
        "notes": "Disabled non-production placeholder; replace before production handoff.",
    },
]
ALLOWED_ALERT_SINK_STUB_KEYS_BY_TYPE = {
    stub["type"]: set(stub)
    for stub in EXPECTED_ALERT_SINK_STUBS
}
PLACEHOLDER_ADDRESS_FIELDS = {
    "placeholder_recipient",
    "placeholder_webhook_url",
    "placeholder_channel",
}
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
    EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH,
}
ZERO_VIOLATION_SAMPLE = []
COMPLIANT_ONLY_SAMPLE = [
    {"class_name": "Person"},
    {"class_name": "Hardhat"},
    {"class_name": "Safety Vest"},
    {"class_name": "Mask"},
]
NEAR_MISS_SAMPLE = [
    {"class_name": "Person"},
    {"class_name": "No-Hardhat"},
    {"class_name": "Safety-Vest-Missing"},
    {"class_name": "no_mask"},
]
POSITIVE_NONCOMPLIANCE_SAMPLE = [
    {"class_name": "Person"},
    {"class_name": "NO-Hardhat"},
    {"class_name": "Safety Vest"},
    {"class_name": "NO-Safety Vest"},
    {"class_name": "NO-Mask"},
]
CLASS_EXPANDED_DUPLICATE_ACTIVE_LEARNING_SAMPLE = [
    {
        "dedupe_key": "site-a/camera-7/frame-0042/window-001",
        "noncompliance_class": "NO-Hardhat",
        "noncompliance_reason": "missing hardhat",
        "source_detection": {"class_name": "NO-Hardhat", "detection_id": "det-hardhat"},
    },
    {
        "dedupe_key": "site-a/camera-7/frame-0042/window-001",
        "noncompliance_class": "NO-Mask",
        "noncompliance_reason": "missing mask",
        "source_detection": {"class_name": "NO-Mask", "detection_id": "det-mask"},
    },
    {
        "dedupe_key": "site-a/camera-7/frame-0042/window-001",
        "noncompliance_class": "NO-Safety Vest",
        "noncompliance_reason": "missing safety vest",
        "source_detection": {"class_name": "NO-Safety Vest", "detection_id": "det-vest"},
    },
]
DISTINCT_EVENT_ACTIVE_LEARNING_SAMPLE = [
    {
        "dedupe_key": "site-a/camera-7/frame-0042/window-001",
        "noncompliance_class": "NO-Hardhat",
        "noncompliance_reason": "missing hardhat",
        "source_detection": {"class_name": "NO-Hardhat", "detection_id": "det-hardhat-42"},
    },
    {
        "dedupe_key": "site-a/camera-7/frame-0043/window-001",
        "noncompliance_class": "NO-Hardhat",
        "noncompliance_reason": "missing hardhat",
        "source_detection": {"class_name": "NO-Hardhat", "detection_id": "det-hardhat-43"},
    },
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
    if sink != EXPECTED_ACTIVE_LEARNING_SINK:
        print(f"unexpected active learning sink target: {sink!r}", file=sys.stderr)
        return False
    return True


def validate_alert_sink_stubs(contract: dict[str, object]) -> bool:
    stubs = contract.get("alert_sink_stubs")
    if not isinstance(stubs, list):
        print("missing alert_sink_stubs list", file=sys.stderr)
        return False
    if stubs != EXPECTED_ALERT_SINK_STUBS:
        print(f"unexpected alert sink stubs: {stubs!r}", file=sys.stderr)
        return False

    seen_types = set()
    for stub in stubs:
        if not isinstance(stub, dict):
            print(f"unexpected alert sink stub shape: {stub!r}", file=sys.stderr)
            return False

        stub_type = stub.get("type")
        seen_types.add(stub_type)
        allowed_keys = ALLOWED_ALERT_SINK_STUB_KEYS_BY_TYPE.get(stub_type)
        if allowed_keys is None:
            print(f"unexpected alert sink stub type: {stub_type!r}", file=sys.stderr)
            return False
        extra_keys = set(stub) - allowed_keys
        missing_keys = allowed_keys - set(stub)
        if extra_keys or missing_keys:
            print(
                "unexpected alert sink stub keys: "
                f"type={stub_type!r}, extra={sorted(extra_keys)!r}, missing={sorted(missing_keys)!r}",
                file=sys.stderr,
            )
            return False

        if stub.get("enabled") is not False or stub.get("sends_live_notifications") is not False:
            print(f"alert sink stub must remain disabled/test-only: {stub!r}", file=sys.stderr)
            return False
        if stub.get("environment") != "test_only" or stub.get("delivery_mode") != "disabled":
            print(f"alert sink stub must declare disabled test-only delivery: {stub!r}", file=sys.stderr)
            return False
        if stub.get("gate_output") != EXPECTED_VIOLATION_EXPRESSION_OUTPUT_NAME:
            print(f"alert sink stub must be gated by has_violations: {stub!r}", file=sys.stderr)
            return False
        if stub.get("source_output") != EXPECTED_VIOLATIONS_OUTPUT_NAME:
            print(f"alert sink stub must source ppe_violations: {stub!r}", file=sys.stderr)
            return False

        for field in PLACEHOLDER_ADDRESS_FIELDS & set(stub):
            value = str(stub.get(field, ""))
            if "placeholder" not in value.lower() and not value.endswith("@example.invalid"):
                print(f"alert sink field must use placeholder-only value: {field}={value!r}", file=sys.stderr)
                return False
            if re.search(r"(xox[baprs]-|hooks\.slack\.com|api[_-]?key|secret|token)", value, re.IGNORECASE):
                print(f"alert sink field looks like a live secret or endpoint: {field}={value!r}", file=sys.stderr)
                return False
        subject = str(stub.get("placeholder_subject", ""))
        if "placeholder_subject" in stub and "[TEST ONLY]" not in subject:
            print(f"email alert subject must be explicitly test-only: {subject!r}", file=sys.stderr)
            return False

    if seen_types != {"email", "slack"}:
        print(f"expected email and slack alert sink stubs, found {sorted(seen_types)!r}", file=sys.stderr)
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


def detections_count_contract_result(detections: list[dict[str, object]]) -> tuple[list[dict[str, object]], int, bool]:
    ppe_violations = [
        detection
        for detection in detections
        if detection.get("class_name") in EXPECTED_VIOLATION_CLASSES
    ]
    violations = len(ppe_violations)
    return ppe_violations, violations, violations > 0


def post_expression_positive_result(
    ppe_violations: list[dict[str, object]],
    has_violations: bool,
) -> list[dict[str, object]]:
    return ppe_violations if has_violations else []


def append_unique(values: list[object], value: object) -> None:
    if value not in values:
        values.append(value)


def collapse_active_learning_records(
    records: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[str]]:
    examples_by_key: dict[str, dict[str, object]] = {}
    errors: list[str] = []

    for index, record in enumerate(records):
        dedupe_key = record.get("dedupe_key")
        if not isinstance(dedupe_key, str) or not dedupe_key.strip():
            errors.append(f"record {index} missing non-empty dedupe_key")
            continue
        if dedupe_key != dedupe_key.strip():
            errors.append(f"record {index} dedupe_key must be canonical")
            continue

        noncompliance_class = record.get("noncompliance_class")
        if not isinstance(noncompliance_class, str) or not noncompliance_class.strip():
            errors.append(f"record {index} missing non-empty noncompliance_class")
            continue
        noncompliance_reason = record.get("noncompliance_reason")
        if not isinstance(noncompliance_reason, str) or not noncompliance_reason.strip():
            errors.append(f"record {index} missing non-empty noncompliance_reason")
            continue
        source_detection = record.get("source_detection")
        if not isinstance(source_detection, dict):
            errors.append(f"record {index} missing source_detection metadata")
            continue

        example = examples_by_key.setdefault(
            dedupe_key,
            {
                "dedupe_key": dedupe_key,
                "noncompliance_classes": [],
                "noncompliance_reasons": [],
                "source_detections": [],
            },
        )
        append_unique(
            example["noncompliance_classes"],
            noncompliance_class,
        )
        append_unique(
            example["noncompliance_reasons"],
            noncompliance_reason,
        )
        append_unique(
            example["source_detections"],
            source_detection,
        )

    return list(examples_by_key.values()), errors


def validate_sample_cases() -> bool:
    expected_cases: list[
        tuple[str, list[dict[str, object]], int, bool, list[dict[str, object]]]
    ] = [
        ("zero ppe_violations", ZERO_VIOLATION_SAMPLE, 0, False, []),
        ("compliant-only detections", COMPLIANT_ONLY_SAMPLE, 0, False, []),
        ("near-miss noncontract class names", NEAR_MISS_SAMPLE, 0, False, []),
        (
            "positive noncompliance detections",
            POSITIVE_NONCOMPLIANCE_SAMPLE,
            3,
            True,
            [
                {"class_name": "NO-Hardhat"},
                {"class_name": "NO-Safety Vest"},
                {"class_name": "NO-Mask"},
            ],
        ),
    ]
    for (
        name,
        detections,
        expected_violations,
        expected_has_violations,
        expected_positive_output,
    ) in expected_cases:
        ppe_violations, violations, has_violations = detections_count_contract_result(detections)
        if violations != expected_violations or has_violations != expected_has_violations:
            print(
                f"unexpected sample result for {name}: "
                f"violations={violations!r}, has_violations={has_violations!r}",
                file=sys.stderr,
            )
            return False
        positive_output = post_expression_positive_result(ppe_violations, has_violations)
        if positive_output != expected_positive_output:
            print(
                f"unexpected post-expression positive output for {name}: {positive_output!r}",
                file=sys.stderr,
            )
            return False
    return True


def validate_active_learning_dedupe_cases() -> bool:
    missing_key_examples, missing_key_errors = collapse_active_learning_records(
        [
            {
                "noncompliance_class": "NO-Hardhat",
                "noncompliance_reason": "missing hardhat",
                "source_detection": {"class_name": "NO-Hardhat"},
            }
        ]
    )
    if missing_key_examples or missing_key_errors != ["record 0 missing non-empty dedupe_key"]:
        print(
            "missing dedupe_key sample did not fail active-learning validation",
            file=sys.stderr,
        )
        return False

    empty_key_examples, empty_key_errors = collapse_active_learning_records(
        [
            {
                "dedupe_key": " ",
                "noncompliance_class": "NO-Mask",
                "noncompliance_reason": "missing mask",
                "source_detection": {"class_name": "NO-Mask"},
            }
        ]
    )
    if empty_key_examples or empty_key_errors != ["record 0 missing non-empty dedupe_key"]:
        print(
            "empty dedupe_key sample did not fail active-learning validation",
            file=sys.stderr,
        )
        return False

    whitespace_key_examples, whitespace_key_errors = collapse_active_learning_records(
        [
            {
                "dedupe_key": " site-a/camera-7/frame-0042/window-001 ",
                "noncompliance_class": "NO-Mask",
                "noncompliance_reason": "missing mask",
                "source_detection": {"class_name": "NO-Mask"},
            }
        ]
    )
    if whitespace_key_examples or whitespace_key_errors != [
        "record 0 dedupe_key must be canonical"
    ]:
        print(
            "non-canonical dedupe_key sample did not fail active-learning validation",
            file=sys.stderr,
        )
        return False

    missing_metadata_examples, missing_metadata_errors = collapse_active_learning_records(
        [
            {
                "dedupe_key": "site-a/camera-7/frame-0042/window-001",
                "noncompliance_class": "NO-Mask",
            }
        ]
    )
    if missing_metadata_examples or missing_metadata_errors != [
        "record 0 missing non-empty noncompliance_reason"
    ]:
        print(
            "missing active-learning metadata sample did not fail validation",
            file=sys.stderr,
        )
        return False

    collapsed_examples, collapse_errors = collapse_active_learning_records(
        CLASS_EXPANDED_DUPLICATE_ACTIVE_LEARNING_SAMPLE
    )
    expected_collapsed_examples = [
        {
            "dedupe_key": "site-a/camera-7/frame-0042/window-001",
            "noncompliance_classes": ["NO-Hardhat", "NO-Mask", "NO-Safety Vest"],
            "noncompliance_reasons": [
                "missing hardhat",
                "missing mask",
                "missing safety vest",
            ],
            "source_detections": [
                {"class_name": "NO-Hardhat", "detection_id": "det-hardhat"},
                {"class_name": "NO-Mask", "detection_id": "det-mask"},
                {"class_name": "NO-Safety Vest", "detection_id": "det-vest"},
            ],
        }
    ]
    if collapse_errors or collapsed_examples != expected_collapsed_examples:
        print(
            f"unexpected active-learning collapse result: {collapsed_examples!r}",
            file=sys.stderr,
        )
        return False

    distinct_examples, distinct_errors = collapse_active_learning_records(
        DISTINCT_EVENT_ACTIVE_LEARNING_SAMPLE
    )
    if distinct_errors or len(distinct_examples) != 2:
        print(
            "distinct positive frame/source events should remain separate active-learning examples",
            file=sys.stderr,
        )
        return False

    return True


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text())
    if not validate_active_learning_sink(contract):
        return 1
    if not validate_alert_sink_stubs(contract):
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
        "post_expression_positive_branch": EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH,
        "active_learning_dedupe_key": "dedupe_key",
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
    post_expression_positive = get_one_step(steps, EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH)
    required_steps = (
        detection,
        violation_filter,
        violation_count,
        violation_expression,
        post_expression_positive,
    )
    if not all(required_steps):
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

    if post_expression_positive.get("type") != "roboflow_core/expression@v1":
        print(
            f"unexpected post-expression positive branch type: {post_expression_positive.get('type')!r}",
            file=sys.stderr,
        )
        return 1
    if post_expression_positive.get("data") != {
        "has_violations": f"$steps.{EXPECTED_VIOLATION_EXPRESSION_BLOCK}.output",
        "ppe_violations": f"$steps.{EXPECTED_VIOLATION_FILTER_BLOCK}.predictions",
    }:
        print(
            f"unexpected post-expression positive branch data: {post_expression_positive.get('data')!r}",
            file=sys.stderr,
        )
        return 1
    expected_post_expression_switch = {
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
                                "operand_name": "has_violations",
                            },
                            "comparator": {"type": "=="},
                            "right_operand": {
                                "type": "StaticOperand",
                                "value": True,
                            },
                        }
                    ],
                },
                "result": {
                    "type": "DynamicCaseResult",
                    "operand_name": "ppe_violations",
                },
            }
        ],
        "default": {
            "type": "StaticCaseResult",
            "value": [],
        },
    }
    if post_expression_positive.get("switch") != expected_post_expression_switch:
        print("unexpected post-expression positive branch switch", file=sys.stderr)
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

    post_expression_outputs = [
        output
        for output in outputs
        if output.get("name") == EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH
        and output.get("type") == EXPECTED_OUTPUT_TYPE
        and output.get("selector") == f"$steps.{EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH}.output"
    ]
    if len(post_expression_outputs) != 1:
        print(
            "missing expected post-expression positive output contract: "
            f"(name={EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH!r}, type={EXPECTED_OUTPUT_TYPE!r}, "
            f"selector='$steps.{EXPECTED_POST_EXPRESSION_POSITIVE_BRANCH}.output')",
            file=sys.stderr,
        )
        return 1

    if not validate_sample_cases():
        return 1
    if not validate_active_learning_dedupe_cases():
        return 1

    print("roboflow workflow contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
