from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..common.io import read_json, read_ndjson
from ..config.paths import DOWNLOADS_DIR, ROOT, SOURCE_DIRS
from ..common.text import normalize_space, slugify


@dataclass(frozen=True)
class SourceRecord:
    source: str
    path: Path
    payload: dict[str, Any]


@dataclass(frozen=True)
class DownloadIndex:
    by_basename: dict[str, list[Path]]


def load_records() -> list[SourceRecord]:
    records: list[SourceRecord] = []
    for source, source_dir in SOURCE_DIRS.items():
        if not source_dir.exists():
            continue

        ndjson_path = source_dir / "records.ndjson"
        if ndjson_path.exists():
            for payload in read_ndjson(ndjson_path):
                records.append(SourceRecord(source, ndjson_path, payload))
            continue

        for path in sorted(source_dir.glob("*.json")):
            records.append(SourceRecord(source, path, read_json(path)))
    return records


def build_download_index() -> DownloadIndex:
    by_basename: dict[str, list[Path]] = defaultdict(list)
    if DOWNLOADS_DIR.exists():
        for path in DOWNLOADS_DIR.rglob("*"):
            if path.is_file():
                by_basename[path.name].append(path)
    return DownloadIndex(by_basename=dict(by_basename))


def parse_year(*values: str | None) -> str | None:
    for value in values:
        match = re.search(r"(19|20)\d{2}", value or "")
        if match:
            return match.group(0)
    return None


def normalize_date(value: str | None) -> str | None:
    value = normalize_space(value)
    if not value:
        return None

    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    months = {
        "januari": "01",
        "februari": "02",
        "maret": "03",
        "april": "04",
        "mei": "05",
        "juni": "06",
        "juli": "07",
        "agustus": "08",
        "september": "09",
        "oktober": "10",
        "november": "11",
        "desember": "12",
    }
    match = re.search(
        r"(\d{1,2})\s+("
        + "|".join(months)
        + r")\s+((?:19|20)\d{2})",
        value.lower(),
    )
    if match:
        day, month_name, year = match.groups()
        return f"{year}-{months[month_name]}-{int(day):02d}"

    return value


def normalize_regulation_type(value: str | None, title: str | None = None) -> str | None:
    joined = f"{value or ''} {title or ''}".upper()
    patterns = [
        "SEOJK",
        "POJK",
        "PADK",
        "PBI",
        "PADG",
        "SEBI",
        "UU",
        "PP",
        "PMK",
        "SK DIR",
    ]
    for pattern in patterns:
        if pattern in joined:
            return pattern
    return normalize_space(value) or None


def normalize_number(number: str | None, title: str | None = None) -> str | None:
    value = normalize_space(number)
    if not value:
        title_value = normalize_space(title)
        patterns = [
            r"(?:No\.?|Nomor)\s*([0-9]+(?:/[A-Za-z0-9.\-]+)*/(?:19|20)\d{2})",
            r"(?:No\.?|Nomor)\s*([0-9]+)\s*Tahun\s*((?:19|20)\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, title_value, flags=re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return f"{match.group(1)} Tahun {match.group(2)}".lower()
                return match.group(1).lower()
        return None

    value = value.replace("\\", "/")
    value = re.sub(r"\s+", " ", value)
    return value.lower()


def regulation_match_key(
    issuer: str | None,
    regulation_type: str | None,
    number: str | None,
    year: str | None,
    include_year: bool = True,
) -> str | None:
    normalized_number = normalize_number(number)
    if not issuer or not normalized_number:
        return None
    normalized_type = normalize_regulation_type(regulation_type) or ""
    parts = [issuer.upper(), normalized_type.upper(), normalized_number]
    if include_year:
        parts.append(str(year or ""))
    return "|".join(parts)


def canonical_id(issuer: str, regulation_type: str | None, number: str | None, year: str | None, title: str) -> str:
    if regulation_type and number:
        base = f"{issuer}:{regulation_type}:{number}"
        if year and year not in number:
            base = f"{base}:{year}"
    else:
        base = f"{issuer}:unknown:{title}"
    return slugify(base)


def file_entries(record: SourceRecord) -> list[dict[str, Any]]:
    payload = record.payload
    if isinstance(payload.get("files"), list):
        return payload["files"]
    if isinstance(payload.get("file"), dict):
        file_payload = dict(payload["file"])
        file_payload.setdefault("kind", payload.get("tab_name") or "file")
        return [file_payload]
    return []


def resolve_saved_path(saved_path: str | None, download_index: DownloadIndex) -> tuple[str | None, bool, str | None]:
    if not saved_path:
        return None, False, "missing_saved_path"

    raw = Path(saved_path)
    candidates = [ROOT / raw]

    if saved_path.startswith("downloads/ojk/"):
        candidates.append(ROOT / saved_path.replace("downloads/ojk/", "downloads/peraturan-ojk/", 1))

    basename = raw.name
    if basename:
        candidates.extend(download_index.by_basename.get(basename, []))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate.relative_to(ROOT)), True, None

    return saved_path, False, "file_not_found"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def source_identity(record: SourceRecord) -> str:
    payload = record.payload
    return (
        payload.get("record_id")
        or payload.get("law_id")
        or payload.get("header_id")
        or payload.get("source_url")
        or payload.get("detail_url")
        or record.path.stem
    )


def issuer_for(record: SourceRecord) -> str:
    if record.source == "ease-bi":
        return "BI"
    return "OJK"


def normalized_metadata(record: SourceRecord) -> dict[str, Any]:
    payload = record.payload
    title = normalize_space(payload.get("title"))
    reg_type = normalize_regulation_type(payload.get("regulation_type"), title)
    number = normalize_number(payload.get("number"), title)
    year = payload.get("year") or parse_year(payload.get("effective_date"), payload.get("date"), number, title)
    effective_date = normalize_date(payload.get("effective_date") or payload.get("date"))
    issuer = issuer_for(record)

    return {
        "canonical_id": canonical_id(issuer, reg_type, number, year, title),
        "issuer": issuer,
        "source": record.source,
        "source_id": source_identity(record),
        "title": title,
        "regulation_type": reg_type,
        "number": number,
        "year": year,
        "effective_date": effective_date,
        "sector": payload.get("sector"),
        "sub_sector": payload.get("sub_sector"),
        "bank_slug": payload.get("bank_slug"),
        "bank_name": payload.get("bank_name"),
        "group_path": payload.get("group_path") or payload.get("list_item", {}).get("group_path"),
        "source_url": payload.get("detail_url") or payload.get("source_url") or payload.get("list_item", {}).get("full_text_url"),
        "fetched_at": payload.get("fetched_at"),
    }


def classify_file_role(source: str, entry: dict[str, Any]) -> str:
    kind = normalize_space(entry.get("kind")).lower()
    label = normalize_space(entry.get("label")).lower()
    haystack = f"{kind} {label}"
    if "faq" in haystack or "ringkasan" in haystack or "infografis" in haystack:
        return "secondary_faq"
    if "abstrak" in haystack or "summary" in haystack or "ringkasan" in haystack:
        return "secondary_summary"
    if "lampiran" in haystack:
        return "attachment"
    if source == "ease-bi" and any(term in haystack for term in ("dokumen", "pedoman", "persyaratan", "matriks")):
        return "operational_requirement"
    return "primary_regulation"
