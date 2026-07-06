from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import load_settings
from app.core.paths import project_root


@dataclass(frozen=True)
class LhPaths:
    root: Path
    input_folder: Path
    capture_exe: Path
    capture_script: Path
    report_script: Path
    python_exe: Path


def resolve_path(relative_path: str) -> Path:
    return project_root() / relative_path


def lh_paths(settings: dict[str, Any]) -> LhPaths:
    lh_root = resolve_path(settings["lh"]["folder"])
    project_venv_python = project_root() / ".venv" / "Scripts" / "python.exe"
    legacy_venv_python = lh_root / ".venv" / "Scripts" / "python.exe"
    if project_venv_python.exists():
        python_exe = project_venv_python
    elif legacy_venv_python.exists():
        python_exe = legacy_venv_python
    else:
        python_exe = Path(sys.executable)
    return LhPaths(
        root=lh_root,
        input_folder=resolve_path(settings["lh"].get("input_folder", settings["lh"]["folder"])),
        capture_exe=resolve_path(settings["lh"]["capture_exe"]),
        capture_script=resolve_path(settings["lh"].get("capture_script", "lh/screen_scraper_gui.py")),
        report_script=resolve_path(settings["lh"]["report_script"]),
        python_exe=python_exe,
    )


def check_layout(paths: LhPaths) -> list[str]:
    missing: list[str] = []
    if not paths.root.exists():
        missing.append(f"LH folder not found: {paths.root}")
    if not paths.input_folder.exists():
        missing.append(f"LH input folder not found: {paths.input_folder}")
    if not paths.capture_exe.exists() and not paths.capture_script.exists():
        missing.append(f"Capture tool not found: {paths.capture_exe} or {paths.capture_script}")
    if not paths.report_script.exists():
        missing.append(f"Report script not found: {paths.report_script}")
    if not paths.python_exe.exists():
        missing.append(f"Python executable not found: {paths.python_exe}")
    return missing



LEGACY_REPORT_ALIASES = {
    "서울": ("서울", "서울지역본부"),
    "경기북부": ("경기북부",),
    "경기남부": ("경기남부",),
}

REGION_SUFFIX_RE = re.compile(r"(?:지역본부|본부|광역시|특별시|특별자치시|특별자치도|도|시)$")
NON_REGION_WORDS = {"당첨자", "당점자", "예비자", "신청자", "공급호수", "모집인원", "주택형", "바로보기", "다운로드"}
BROAD_REGION_PREFIXES = ("경기북부", "경기남부", "부산울산", "서울", "경기", "인천", "부산", "울산", "대구", "광주", "대전", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주")


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def clean_ocr_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_region_candidate(value: str) -> str:
    value = REGION_SUFFIX_RE.sub("", clean_ocr_text(value))
    value = re.sub(r"[^가-힣]", "", value)
    for prefix in BROAD_REGION_PREFIXES:
        if value.startswith(prefix):
            return prefix
    return value


def report_key_from_text(text: str) -> str:
    compact = compact_text(text)
    for key, aliases in LEGACY_REPORT_ALIASES.items():
        if any(alias in compact for alias in aliases):
            return key
    return ""


def extract_lh_title_hint(text: str) -> str:
    lines = [clean_ocr_text(line) for line in str(text or "").splitlines()]
    candidates = []
    for line in lines:
        compact = compact_text(line)
        if "든든전세" in compact and ("공고" in compact or "입주자" in compact or "모집" in compact):
            candidates.append(line)
    if candidates:
        return max(candidates, key=len)

    compact = compact_text(text)
    match = re.search(r"(.{0,30}든든전세.{0,45}(?:공고|모집))", compact)
    return match.group(1) if match else ""


def extract_lh_region_hint(text: str, title_hint: str = "") -> str:
    evidence = "\n".join(part for part in (title_hint, str(text or "")) if part)
    compact_evidence = compact_text(evidence)
    for pattern in (r"모집지역[:：]?([가-힣]{2,12})", r"공고([가-힣]{2,12})\)"):
        match = re.search(pattern, compact_evidence)
        if match:
            value = normalize_region_candidate(match.group(1))
            if value and value not in NON_REGION_WORDS:
                return value

    for pattern in (r"\[([^\]]{1,20})\]", r"\(([^)]{1,20})\)"):
        for match in re.finditer(pattern, evidence):
            value = normalize_region_candidate(match.group(1))
            if value and value not in NON_REGION_WORDS and not re.search(r"\d|차|공고|모집|주택|전세", value):
                return value

    compact = compact_text(title_hint or text)
    match = re.search(r"\d+년\d*차?([가-힣]{2,12})(?:비분양|든든전세|매입임대)", compact)
    if match:
        value = normalize_region_candidate(match.group(1))
        if value and value not in NON_REGION_WORDS:
            return value
    return report_key_from_text(evidence)


def read_lh_image_text(path: Path) -> str:
    warnings.filterwarnings("ignore", message=".*pin_memory.*", category=UserWarning)
    try:
        model_dir = project_root() / "app" / "cache" / "easyocr"
        model_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("EASYOCR_MODULE_PATH", str(model_dir))
        import cv2
        import easyocr
        import numpy as np
    except Exception:
        return ""
    try:
        raw = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if image is None:
            return ""
        crop = image[: min(image.shape[0], 2400), :]
        reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        texts = reader.readtext(crop, detail=0, paragraph=True)
        return "\n".join(str(item) for item in texts)
    except Exception:
        return ""


def build_detection_payload(path: Path) -> dict[str, str]:
    image_text = read_lh_image_text(path)
    title_hint = extract_lh_title_hint(image_text)
    region_hint = extract_lh_region_hint(image_text, title_hint)
    legacy_key = report_key_from_text("\n".join([title_hint, image_text, path.stem]))
    return {
        "image_text": image_text,
        "title_hint": title_hint,
        "region_hint": region_hint,
        "legacy_key": legacy_key,
        "detected_by": "PNG 내부 공고 문구 OCR",
    }


def prepare_detected_regions(paths: LhPaths) -> None:
    detections: dict[str, dict[str, str]] = {}
    for path in png_inputs(paths):
        payload = build_detection_payload(path)
        if payload["image_text"] or payload["title_hint"] or payload["region_hint"] or payload["legacy_key"]:
            detections[path.name] = payload
    manifest = paths.input_folder / "_detected_regions.json"
    manifest.write_text(json.dumps(detections, ensure_ascii=False, indent=2), encoding="utf-8")

def png_inputs(paths: LhPaths) -> list[Path]:
    return sorted(paths.input_folder.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)


def launch_capture(paths: LhPaths) -> subprocess.Popen[bytes]:
    paths.input_folder.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "LH_CAPTURE_OUTPUT_DIR": str(paths.input_folder)}
    if paths.capture_script.exists():
        return subprocess.Popen([sys.executable, str(paths.capture_script)], cwd=str(paths.root), env=env)
    return subprocess.Popen([str(paths.capture_exe)], cwd=str(paths.input_folder), env=env)


def run_report_details(paths: LhPaths) -> tuple[int, str]:
    prepare_detected_regions(paths)
    env = {**os.environ, "PYTHONUTF8": "1"}
    completed = subprocess.run(
        [str(paths.python_exe), str(paths.report_script)],
        cwd=str(paths.root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return completed.returncode, output


def run_report(paths: LhPaths) -> int:
    code, output = run_report_details(paths)
    if output:
        print(output)
    return code


def print_layout(paths: LhPaths) -> None:
    print(f"LH root: {paths.root}")
    print(f"LH input folder: {paths.input_folder}")
    print(f"Capture executable: {paths.capture_exe}")
    print(f"Capture script: {paths.capture_script}")
    print(f"Report script: {paths.report_script}")
    print(f"Python executable: {paths.python_exe}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run existing LH screenshot/report workflow.")
    parser.add_argument("--check", action="store_true", help="Check required LH paths.")
    parser.add_argument("--list-inputs", action="store_true", help="List PNG files visible to LH report script.")
    parser.add_argument("--capture", action="store_true", help="Launch the existing screenshot tool.")
    parser.add_argument("--run-report", action="store_true", help="Run the existing LH report script.")
    args = parser.parse_args()

    settings = load_settings()
    paths = lh_paths(settings)
    if args.check or not any((args.list_inputs, args.capture, args.run_report)):
        print_layout(paths)
        missing = check_layout(paths)
        if missing:
            print("Missing required LH files:")
            for item in missing:
                print(f"- {item}")
            return 1
        print("LH required files: OK")

    if args.list_inputs:
        inputs = png_inputs(paths)
        print(f"PNG inputs: {len(inputs)}")
        for path in inputs:
            print(f"- {path.name}")

    if args.capture:
        launch_capture(paths)
        print("Capture tool launched.")

    if args.run_report:
        return run_report(paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())







