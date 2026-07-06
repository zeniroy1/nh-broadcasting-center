from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.core.paths import app_root


def metrics_registry_path() -> Path:
    return app_root() / "config" / "metrics_registry.json"


def normalize_label(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"Unnamed:\s*\d+(?:_level_\d+)?", "", text, flags=re.I)
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text).lower()


def flatten_label(value: object) -> str:
    if isinstance(value, tuple):
        parts = [str(part) for part in value if str(part) and not str(part).startswith("Unnamed:")]
        return " ".join(parts)
    return str(value or "")


@dataclass(frozen=True)
class MetricMatch:
    original: str
    metric_id: str
    label: str
    value_type: str


class MetricRegistry:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.metrics: dict[str, dict[str, Any]] = data.get("metrics", {})

    def alias_index(self, source: str | None = None) -> dict[str, str]:
        index: dict[str, str] = {}
        source_key = (source or "").lower()
        for metric_id, metric in self.metrics.items():
            aliases = list(metric.get("aliases", []))
            aliases.append(metric.get("label", metric_id))
            source_aliases = metric.get("source_aliases", {})
            if source_key and isinstance(source_aliases, dict):
                aliases.extend(source_aliases.get(source_key, []))
            for alias in aliases:
                key = normalize_label(alias)
                if key:
                    index[key] = metric_id
        return index

    def resolve(self, label: object, source: str | None = None) -> str | None:
        key = normalize_label(flatten_label(label))
        return self.alias_index(source).get(key)

    def map_labels(self, labels: Iterable[object], source: str | None = None) -> dict[str, MetricMatch]:
        mapped: dict[str, MetricMatch] = {}
        for label in labels:
            original = flatten_label(label)
            metric_id = self.resolve(original, source)
            if not metric_id:
                continue
            metric = self.metrics[metric_id]
            mapped[original] = MetricMatch(
                original=original,
                metric_id=metric_id,
                label=str(metric.get("label", metric_id)),
                value_type=str(metric.get("type", "text")),
            )
        return mapped

    def matched_metric_ids(self, labels: Iterable[object], source: str | None = None) -> set[str]:
        return {match.metric_id for match in self.map_labels(labels, source).values()}

    def has_required_set(self, labels: Iterable[object], required_set: str, source: str | None = None) -> bool:
        required = set(self.data.get("required_sets", {}).get(required_set, []))
        if not required:
            return False
        return required.issubset(self.matched_metric_ids(labels, source))

    def profile_record(self, record: dict[str, Any], source: str | None = None) -> dict[str, Any]:
        standard: dict[str, Any] = {}
        extra: dict[str, Any] = {}
        for key, value in record.items():
            metric_id = self.resolve(key, source)
            if metric_id:
                standard[metric_id] = value
            else:
                extra[key] = value
        return {"standard": standard, "extra": extra}

    def summary(self) -> dict[str, Any]:
        return {
            "path": str(metrics_registry_path()),
            "version": self.data.get("version"),
            "metricCount": len(self.metrics),
            "requiredSets": self.data.get("required_sets", {}),
            "futureSources": self.data.get("future_sources", {}),
        }


def load_metric_registry() -> MetricRegistry:
    with metrics_registry_path().open("r", encoding="utf-8") as file:
        return MetricRegistry(json.load(file))
