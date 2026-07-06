"""Audit the Musinsa roadmap plugin deliverables across all completed steps."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SRC_ROOT = Path(__file__).resolve().parents[1]
STEP_RANGE = range(1, 11)
COMPLETED_IMPLEMENTATION_STEPS = range(1, 10)
REQUIRED_BOUNDARY_TERMS = [
    "실제 구매자 수",
    "실제 판매",
    "실제 반품률",
    "confidence_percent",
    "타겟 적합도",
]


@dataclass(frozen=True)
class AuditCheck:
    key: str
    label: str
    status: str
    detail: str


def _exists(relative_path: str) -> bool:
    return (SRC_ROOT / relative_path).exists()


def _read_text(relative_path: str) -> str:
    return (SRC_ROOT / relative_path).read_text(encoding="utf-8")


def _line_count(relative_path: str) -> int:
    return len(_read_text(relative_path).splitlines())


def _check_plugin_structure() -> AuditCheck:
    required = [
        ".codex-plugin/plugin.json",
        "skills/musinsa-product-roadmap/SKILL.md",
        "docs/musinsa_search_parsing_roadmap.md",
    ]
    missing = [path for path in required if not _exists(path)]
    if missing:
        return AuditCheck("plugin_structure", "플러그인 구조", "fail", f"missing: {missing}")
    manifest = json.loads(_read_text(".codex-plugin/plugin.json"))
    if manifest.get("name") != "musinsa-product-roadmap":
        return AuditCheck("plugin_structure", "플러그인 구조", "fail", "plugin name mismatch")
    return AuditCheck("plugin_structure", "플러그인 구조", "pass", "plugin.json, SKILL.md, roadmap present")


def _check_step_documents() -> AuditCheck:
    missing: list[str] = []
    for step in STEP_RANGE:
        doc = f"docs/step_{step:02d}_{_step_slug(step)}.md"
        review = f"docs/step_{step:02d}_self_review.md"
        if not _exists(doc):
            missing.append(doc)
        if not _exists(review):
            missing.append(review)
    if missing:
        return AuditCheck("step_documents", "단계 문서", "fail", f"missing: {missing}")
    return AuditCheck("step_documents", "단계 문서", "pass", "step 01-10 docs and self reviews present")


def _check_step_reports() -> AuditCheck:
    missing: list[str] = []
    for step in STEP_RANGE:
        slug = _step_slug(step)
        html = f"reports/step_{step:02d}_{slug}_status.html"
        svg = f"reports/step_{step:02d}_{slug}_status.svg"
        if not _exists(html):
            missing.append(html)
        if not _exists(svg):
            missing.append(svg)
    if missing:
        return AuditCheck("step_reports", "HTML/SVG 리포트", "fail", f"missing: {missing}")
    return AuditCheck("step_reports", "HTML/SVG 리포트", "pass", "step 01-10 HTML and SVG reports present")


def _check_tests() -> AuditCheck:
    tests = sorted((SRC_ROOT / "tests").glob("test_*.py"))
    if len(tests) < 11:
        return AuditCheck("test_files", "테스트 파일", "fail", f"test file count too low: {len(tests)}")
    return AuditCheck("test_files", "테스트 파일", "pass", f"{len(tests)} test files present")


def _check_boundary_language() -> AuditCheck:
    combined = "\n".join(
        _read_text(path)
        for path in [
            "docs/step_08_scoring_model.md",
            "docs/step_09_recommendation_output.md",
            "docs/step_10_final_audit.md",
            "docs/development_decision_record.md",
        ]
        if _exists(path)
    )
    missing = [term for term in REQUIRED_BOUNDARY_TERMS if term not in combined]
    if missing:
        return AuditCheck("boundary_language", "내부 데이터 경계", "fail", f"missing terms: {missing}")
    return AuditCheck("boundary_language", "내부 데이터 경계", "pass", "public/proxy boundaries are documented")


def _check_visual_decisions() -> AuditCheck:
    html = _read_text("reports/step_09_recommendation_output_status.html")
    required = ["세로 막대그래프", "타겟 적합도", "베이직", "코튼", "데일리"]
    missing = [term for term in required if term not in html]
    if missing:
        return AuditCheck("visual_decisions", "시각화 UI", "fail", f"missing terms: {missing}")
    return AuditCheck("visual_decisions", "시각화 UI", "pass", "vertical bars and target label are present")


def _check_live_buyer_app() -> AuditCheck:
    required = [
        "scripts/musinsa_live_buyer_app.py",
        "scripts/musinsa_buyer_server.py",
        "tests/test_musinsa_live_buyer_app.py",
        "tests/test_musinsa_buyer_server.py",
        "app/musinsa_buyer_app.html",
        "docs/live_buyer_program.md",
        "docs/live_buyer_program_self_review.md",
        "reports/live_buyer_app_status.html",
        "reports/live_buyer_app_status.svg",
    ]
    missing = [path for path in required if not _exists(path)]
    if missing:
        return AuditCheck("live_buyer_app", "실사용 수집기/UI", "fail", f"missing: {missing}")
    html = _read_text("app/musinsa_buyer_app.html")
    required_terms = ["무신사 제품 검색기", "5개 후보", "3개 후보", "타겟", "상품 보기", "리롤"]
    missing_terms = [term for term in required_terms if term not in html]
    if missing_terms:
        return AuditCheck("live_buyer_app", "실사용 수집기/UI", "fail", f"missing terms: {missing_terms}")
    return AuditCheck("live_buyer_app", "실사용 수집기/UI", "pass", "collector, app UI, reports, and tests present")


def _check_line_counts() -> AuditCheck:
    important = [
        "scripts/musinsa_recommendation_output.py",
        "scripts/musinsa_scoring_model.py",
        "scripts/musinsa_project_audit.py",
        "scripts/musinsa_live_buyer_app.py",
        "scripts/musinsa_buyer_server.py",
        "app/musinsa_buyer_app.html",
        "docs/step_10_final_audit.md",
        "docs/step_10_self_review.md",
        "docs/live_buyer_program.md",
        "docs/live_buyer_program_self_review.md",
        "reports/step_10_final_audit_status.html",
        "reports/step_10_final_audit_status.svg",
        "reports/live_buyer_app_status.html",
        "reports/live_buyer_app_status.svg",
    ]
    counts = {path: _line_count(path) for path in important if _exists(path)}
    if len(counts) != len(important):
        return AuditCheck("line_counts", "라인 수 정리", "fail", f"missing line count targets: {sorted(set(important) - set(counts))}")
    return AuditCheck("line_counts", "라인 수 정리", "pass", json.dumps(counts, ensure_ascii=False))


def _step_slug(step: int) -> str:
    return {
        1: "intent_parser",
        2: "public_signal_catalog",
        3: "proxy_metric_mapping",
        4: "query_candidate_generation",
        5: "collection_scope_planning",
        6: "detail_data_schema",
        7: "review_signal_design",
        8: "scoring_model",
        9: "recommendation_output",
        10: "final_audit",
    }[step]


def build_project_audit() -> dict[str, Any]:
    checks = [
        _check_plugin_structure(),
        _check_step_documents(),
        _check_step_reports(),
        _check_tests(),
        _check_boundary_language(),
        _check_visual_decisions(),
        _check_live_buyer_app(),
        _check_line_counts(),
    ]
    failed = [check for check in checks if check.status != "pass"]
    completed_steps = len(list(COMPLETED_IMPLEMENTATION_STEPS))
    return {
        "audit_version": "0.1.0",
        "completed_implementation_steps": completed_steps,
        "total_roadmap_steps": 10,
        "status": "pass" if not failed else "fail",
        "checks": [asdict(check) for check in checks],
        "failed_checks": [asdict(check) for check in failed],
        "summary": (
            "1~10단계 산출물과 실사용 수집기/UI 산출물이 정합성을 갖춘 상태입니다."
            if not failed
            else "일부 전체 검수 항목이 실패했습니다."
        ),
        "next_step_policy": "사용자 승인 전에는 추가 단계나 제출 zip 업로드를 진행하지 않는다.",
    }


def validate_project_audit() -> list[str]:
    audit = build_project_audit()
    errors: list[str] = []
    if audit["status"] != "pass":
        errors.extend(f"{check['key']}: {check['detail']}" for check in audit["failed_checks"])
    if audit["completed_implementation_steps"] != 9:
        errors.append("completed implementation step count must be 9")
    if audit["total_roadmap_steps"] != 10:
        errors.append("roadmap step count must be 10")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Musinsa roadmap plugin deliverables.")
    parser.add_argument("--validate", action="store_true", help="Validate project audit")
    args = parser.parse_args()

    if args.validate:
        errors = validate_project_audit()
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1 if errors else 0)
    print(json.dumps(build_project_audit(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
