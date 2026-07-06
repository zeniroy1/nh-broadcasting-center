"""Record unknown Musinsa-sourced keywords for reviewed dictionary updates."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
SRC_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from musinsa_runtime_paths import resource_path, writable_path

DEFAULT_QUEUE_PATH = writable_path("config", "keyword_learning_queue.json")
ALIAS_CONFIG_PATH = resource_path("config", "search_keyword_aliases.json")
DEFAULT_QUEUE = {
    "version": "2026-06-30",
    "description": "Pending unknown keyword pool. Terms are collected from public Musinsa keyword sources and must be reviewed before promotion to category or alias dictionaries.",
    "update_policy": {
        "capture": "public_musinsa_keyword_sources",
        "review_cycle": "weekly",
        "promotion_threshold": {"min_count": 3, "min_public_match_count": 5},
        "dedupe_window": "daily_per_source",
    },
    "terms": [],
}

from musinsa_intent_parser import _known_keyword_set


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_term(term: str) -> str:
    return "".join(str(term).casefold().split())


def _today_key(now: str | None) -> str:
    return (now or _now_iso())[:10]


def _alias_terms(path: Path = ALIAS_CONFIG_PATH) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    result: set[str] = set()
    for group in payload.get("aliases", []):
        terms = group.get("terms", []) if isinstance(group, dict) else group
        for term in terms:
            if str(term).strip():
                result.add(str(term).strip())
    return result


def known_dictionary_terms() -> set[str]:
    return {_normalize_term(term) for term in (_known_keyword_set() | _alias_terms()) if _normalize_term(term)}


def is_unknown_dictionary_term(term: str) -> bool:
    key = _normalize_term(term)
    return len(key) >= 2 and key not in known_dictionary_terms()


def load_keyword_learning_queue(path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, Any]:
    queue_path = Path(path)
    if not queue_path.exists():
        return json.loads(json.dumps(DEFAULT_QUEUE, ensure_ascii=False))
    with queue_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    payload.setdefault("terms", [])
    payload.setdefault("update_policy", DEFAULT_QUEUE["update_policy"])
    return payload


def save_keyword_learning_queue(payload: dict[str, Any], path: str | Path = DEFAULT_QUEUE_PATH) -> None:
    queue_path = Path(path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = queue_path.with_suffix(queue_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    tmp_path.replace(queue_path)


def _candidate_terms(intent: dict[str, Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for term in intent.get("free_terms") or []:
        value = str(term).strip()
        key = _normalize_term(value)
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def update_keyword_learning_queue(
    query: str,
    intent: dict[str, Any],
    diagnostics: dict[str, Any],
    path: str | Path = DEFAULT_QUEUE_PATH,
    now: str | None = None,
) -> dict[str, Any]:
    terms = _candidate_terms(intent)
    if not terms:
        return {"updated": 0, "terms": [], "review_ready": []}

    timestamp = now or _now_iso()
    payload = load_keyword_learning_queue(path)
    existing = {_normalize_term(item.get("term", "")): item for item in payload.get("terms", [])}
    counts = diagnostics.get("counts") or {}
    public_match_count = int(counts.get("filtered") or 0) + int(counts.get("similar_candidates") or 0)
    updated_terms: list[str] = []

    for term in terms:
        key = _normalize_term(term)
        item = existing.get(key)
        if item is None:
            item = {
                "term": term,
                "normalized": key,
                "status": "pending_review",
                "count": 0,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "sample_queries": [],
                "last_public_match_count": 0,
                "max_public_match_count": 0,
                "suggested_action": "review_as_alias_or_category_keyword",
            }
            payload["terms"].append(item)
            existing[key] = item
        item["count"] = int(item.get("count") or 0) + 1
        item["last_seen"] = timestamp
        item["last_public_match_count"] = public_match_count
        item["max_public_match_count"] = max(int(item.get("max_public_match_count") or 0), public_match_count)
        samples = list(item.get("sample_queries") or [])
        if query not in samples:
            samples.append(query)
        item["sample_queries"] = samples[-5:]
        threshold = payload.get("update_policy", {}).get("promotion_threshold", {})
        min_count = int(threshold.get("min_count") or 3)
        min_public = int(threshold.get("min_public_match_count") or 5)
        item["promotion_ready"] = item["count"] >= min_count and item["max_public_match_count"] >= min_public
        updated_terms.append(term)

    payload["terms"] = sorted(payload["terms"], key=lambda item: (-int(item.get("count") or 0), item.get("normalized", "")))
    save_keyword_learning_queue(payload, path)
    review_ready = [item["term"] for item in payload["terms"] if item.get("promotion_ready")]
    return {"updated": len(updated_terms), "terms": updated_terms, "review_ready": review_ready}


def update_keyword_discovery_from_terms(
    terms: list[str],
    source: str,
    path: str | Path = DEFAULT_QUEUE_PATH,
    now: str | None = None,
) -> dict[str, Any]:
    timestamp = now or _now_iso()
    date_key = _today_key(timestamp)
    payload = load_keyword_learning_queue(path)
    existing = {_normalize_term(item.get("term", "")): item for item in payload.get("terms", [])}
    updated_terms: list[str] = []

    for raw_term in terms:
        term = str(raw_term).strip()
        key = _normalize_term(term)
        if not is_unknown_dictionary_term(term):
            continue
        item = existing.get(key)
        if item is None:
            item = {
                "term": term,
                "normalized": key,
                "status": "pending_review",
                "count": 0,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "sample_queries": [],
                "last_public_match_count": 0,
                "max_public_match_count": 0,
                "sources": [],
                "seen_dates": [],
                "suggested_action": "review_as_alias_or_category_keyword",
            }
            payload["terms"].append(item)
            existing[key] = item
        source_day_key = f"{source}:{date_key}"
        seen_dates = list(item.get("seen_dates") or [])
        if source_day_key in seen_dates:
            item["last_seen"] = timestamp
            continue
        item["count"] = int(item.get("count") or 0) + 1
        item["last_seen"] = timestamp
        item["sample_queries"] = (list(item.get("sample_queries") or []) + [f"{source}:{term}"])[-5:]
        item["sources"] = sorted(set(list(item.get("sources") or []) + [source]))
        item["seen_dates"] = (seen_dates + [source_day_key])[-30:]
        threshold = payload.get("update_policy", {}).get("promotion_threshold", {})
        min_count = int(threshold.get("min_count") or 3)
        item["promotion_ready"] = item["count"] >= min_count
        updated_terms.append(term)

    if updated_terms:
        payload["terms"] = sorted(payload["terms"], key=lambda item: (-int(item.get("count") or 0), item.get("normalized", "")))
        save_keyword_learning_queue(payload, path)
    review_ready = [item["term"] for item in payload["terms"] if item.get("promotion_ready")]
    return {"updated": len(updated_terms), "terms": updated_terms, "review_ready": review_ready, "source": source}


def summarize_keyword_learning_queue(path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, Any]:
    payload = load_keyword_learning_queue(path)
    terms = payload.get("terms", [])
    return {
        "total_terms": len(terms),
        "pending_review": sum(1 for item in terms if item.get("status") == "pending_review"),
        "promotion_ready": [item.get("term") for item in terms if item.get("promotion_ready")],
        "review_cycle": payload.get("update_policy", {}).get("review_cycle", "weekly"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the Musinsa unknown keyword learning queue.")
    parser.add_argument("--summary", action="store_true", help="Print queue summary")
    parser.add_argument("--path", default=str(DEFAULT_QUEUE_PATH), help="Queue JSON path")
    args = parser.parse_args()
    payload = summarize_keyword_learning_queue(args.path) if args.summary else load_keyword_learning_queue(args.path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
