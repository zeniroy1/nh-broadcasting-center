from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CollectionResult:
    source: str
    region: str
    data_path: Path
    summary_path: Path | None
    row_count: int


class Collector:
    source: str

    def collect(self, region: str) -> CollectionResult:
        raise NotImplementedError
