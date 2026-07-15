from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config.paths import OCR_NEEDED_PATH


@dataclass(frozen=True)
class OcrExclusion:
    file_id: str
    reason: str | None = None

    def __post_init__(self) -> None:
        normalized = self.file_id.strip()
        if not normalized:
            raise ValueError("OCR exclusion file_id is required")
        object.__setattr__(self, "file_id", normalized)
        if self.reason is not None:
            object.__setattr__(self, "reason", self.reason.strip() or None)


@dataclass(frozen=True)
class CorpusCoverage:
    eligible_count: int
    skipped_ocr_file_ids: tuple[str, ...]

    @property
    def skipped_ocr_count(self) -> int:
        return len(self.skipped_ocr_file_ids)


class OcrEligibility:
    """The sole corpus-eligibility authority for the OCR-disabled migration."""

    def __init__(self, exclusions: Iterable[OcrExclusion]) -> None:
        entries = tuple(exclusions)
        ids = [entry.file_id for entry in entries]
        if len(ids) != len(set(ids)):
            raise ValueError("OCR exclusion file IDs must be unique")
        self._by_file_id = {entry.file_id: entry for entry in entries}

    @classmethod
    def load(cls, path: Path = OCR_NEEDED_PATH) -> OcrEligibility:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Missing authoritative OCR exclusion list: {path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid OCR exclusion JSON: {path}") from error
        if not isinstance(payload, list):
            raise ValueError("reports/ocr_needed.json must be a JSON list")
        entries: list[OcrExclusion] = []
        for item in payload:
            if isinstance(item, str):
                entries.append(OcrExclusion(file_id=item))
                continue
            if isinstance(item, Mapping):
                file_id = item.get("file_id")
                if not isinstance(file_id, str):
                    raise ValueError("OCR exclusion objects require a string file_id")
                reason = item.get("reason")
                if reason is not None and not isinstance(reason, str):
                    raise ValueError("OCR exclusion reason must be a string")
                entries.append(OcrExclusion(file_id=file_id, reason=reason))
                continue
            raise ValueError("OCR exclusions must be file ID strings or objects")
        return cls(entries)

    @property
    def exclusions(self) -> tuple[OcrExclusion, ...]:
        return tuple(self._by_file_id.values())

    def is_eligible(self, file_id: str) -> bool:
        return file_id not in self._by_file_id

    def eligible_file_ids(self, file_ids: Iterable[str]) -> tuple[str, ...]:
        return tuple(file_id for file_id in file_ids if self.is_eligible(file_id))

    def coverage(self, file_ids: Iterable[str]) -> CorpusCoverage:
        known = tuple(dict.fromkeys(file_ids))
        skipped = tuple(file_id for file_id in known if not self.is_eligible(file_id))
        return CorpusCoverage(
            eligible_count=len(known) - len(skipped),
            skipped_ocr_file_ids=skipped,
        )

    def validate_raw_record(self, raw_record: Mapping[str, Any]) -> None:
        options = raw_record.get("liteparse_options")
        if not isinstance(options, Mapping):
            return
        if options.get("ocr_enabled") is True:
            file_id = str(raw_record.get("file_id") or "<unknown>")
            raise ValueError(f"Raw extraction for {file_id} used OCR and is ineligible")
