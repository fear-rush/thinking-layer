from __future__ import annotations

import argparse
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from enum import Enum
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import mkdtemp
from typing import Any

from ..config.paths import CORPUS_DIR, OCR_NEEDED_PATH, RAW_LITEPARSE_DIR, ROOT
from ..domain.legal import LifecycleRelation, SourceDocument
from .audit import AuditFinding, CorpusAudit, audit_corpus
from .catalog import Catalog, catalog_raw_record
from .context import assemble_contextual_units
from .eligibility import OcrEligibility
from .lifecycle import LifecycleGraph, extract_lifecycle_relations
from .liteparse_normalizer import MarkdownNormalizationError
from .parser import QuarantinedDocumentError, parse_raw_document


@dataclass(frozen=True)
class CorpusBuildResult:
    output_dir: Path
    source_document_count: int
    node_count: int
    context_count: int
    lifecycle_relation_count: int
    audit: CorpusAudit
    skipped_ocr_file_ids: tuple[str, ...]
    quarantined_sources: tuple[tuple[str, str], ...]
    geometry_disagreements: tuple[tuple[str, str, str], ...]
    manifest_path: Path


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _write_record(handle: Any, record: Any) -> None:
    handle.write(json.dumps(_json_value(record), ensure_ascii=False, sort_keys=True))
    handle.write("\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aggregate_input_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _git_hash() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _load_raw(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid fresh raw JSON: {path}") from error
    if not isinstance(raw, dict):
        raise ValueError(f"fresh raw JSON must be an object: {path}")
    return raw


def _raw_document_paths(raw_dir: Path) -> tuple[Path, ...]:
    """Return fresh document records without treating extraction metadata as input."""

    documents_dir = raw_dir / "documents"
    if documents_dir.exists():
        return tuple(sorted(documents_dir.glob("*.json")))
    return tuple(
        path
        for path in sorted(raw_dir.glob("*.json"))
        if path.name not in {"inventory.json", "manifest.json"}
    )


def _publish_build(staging_dir: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    staging_dir.replace(output_dir)


def build_corpus(
    *,
    raw_dir: Path = RAW_LITEPARSE_DIR,
    output_dir: Path = CORPUS_DIR,
    ocr_needed_path: Path = OCR_NEEDED_PATH,
) -> CorpusBuildResult:
    """Build the only accepted corpus contract from fresh OCR-disabled raw pages."""
    eligibility = OcrEligibility.load(ocr_needed_path)
    raw_paths = _raw_document_paths(raw_dir)
    if not raw_paths:
        raise ValueError(
            f"no fresh raw JSON files found in {raw_dir}; run the OCR-disabled source extraction first"
        )

    source_documents: list[SourceDocument] = []
    relations: list[LifecycleRelation] = []
    findings: list[AuditFinding] = []
    node_count = 0
    context_count = 0
    observed_file_ids: set[str] = set()
    skipped_file_ids: set[str] = set()
    quarantined_sources: dict[str, str] = {}
    geometry_disagreements: list[tuple[str, str, str]] = []

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        documents_path = staging_dir / "source_documents.ndjson"
        nodes_path = staging_dir / "legal_nodes.ndjson"
        contexts_path = staging_dir / "contextual_units.ndjson"
        relations_path = staging_dir / "lifecycle_relations.ndjson"
        with (
            documents_path.open("w", encoding="utf-8") as documents_handle,
            nodes_path.open("w", encoding="utf-8") as nodes_handle,
            contexts_path.open("w", encoding="utf-8") as contexts_handle,
            relations_path.open("w", encoding="utf-8") as relations_handle,
        ):
            for path in raw_paths:
                raw = _load_raw(path)
                file_id = raw.get("file_id")
                if not isinstance(file_id, str) or not file_id.strip():
                    raise ValueError(f"fresh raw document requires file_id: {path}")
                observed_file_ids.add(file_id)
                if not eligibility.is_eligible(file_id):
                    skipped_file_ids.add(file_id)
                    continue
                eligibility.validate_raw_record(raw)
                document = catalog_raw_record(raw, path)
                try:
                    parsed = parse_raw_document(raw)
                except (MarkdownNormalizationError, QuarantinedDocumentError) as error:
                    quarantined_sources[file_id] = error.reason
                    if isinstance(error, QuarantinedDocumentError):
                        geometry_disagreements.extend(
                            (file_id, disagreement.block_id, disagreement.reason)
                            for disagreement in error.geometry_disagreements
                        )
                    continue
                geometry_disagreements.extend(
                    (file_id, disagreement.block_id, disagreement.reason)
                    for disagreement in parsed.geometry_disagreements
                )
                document_contexts = assemble_contextual_units(parsed)
                document_relations = extract_lifecycle_relations(document, parsed.nodes)
                document_audit = audit_corpus(
                    source_documents=(document,),
                    nodes=parsed.nodes,
                    contexts=document_contexts,
                    lifecycle_relations=document_relations,
                )
                findings.extend(document_audit.findings)
                source_documents.append(document)
                relations.extend(document_relations)
                node_count += len(parsed.nodes)
                context_count += len(document_contexts)
                _write_record(documents_handle, document)
                for node in parsed.nodes:
                    _write_record(nodes_handle, node)
                for context in document_contexts:
                    _write_record(contexts_handle, context)
                for relation in document_relations:
                    _write_record(relations_handle, relation)

        try:
            Catalog(tuple(source_documents))
        except ValueError as error:
            findings.append(AuditFinding("catalog_identity", str(error)))
        try:
            LifecycleGraph(tuple(relations))
        except ValueError as error:
            findings.append(AuditFinding("lifecycle_cycle", str(error)))
        audit = CorpusAudit(
            findings=tuple(findings),
            document_count=len(source_documents),
            node_count=node_count,
            context_count=context_count,
            lifecycle_relation_count=len(relations),
        )
        if not audit.passed:
            codes = ", ".join(sorted({finding.code for finding in audit.findings}))
            examples = "; ".join(
                f"{finding.code}: {finding.message} ({', '.join(finding.references)})"
                for finding in audit.findings[:5]
            )
            raise ValueError(
                f"corpus structural audit failed: {codes}. Examples: {examples}"
            )

        reported_ocr_file_ids = tuple(entry.file_id for entry in eligibility.exclusions)
        missing_reported_ids = tuple(
            file_id
            for file_id in reported_ocr_file_ids
            if file_id not in observed_file_ids
        )
        if set(reported_ocr_file_ids) != skipped_file_ids | set(missing_reported_ids):
            raise ValueError("OCR exclusion accounting is inconsistent")

        manifest = {
            "contract": "thinking-layer-corpus-v1",
            "raw_input_count": len(raw_paths),
            "eligible_document_count": len(source_documents),
            "node_count": node_count,
            "context_count": context_count,
            "lifecycle_relation_count": len(relations),
            "skipped_ocr_count": len(reported_ocr_file_ids),
            "skipped_ocr_file_ids": list(reported_ocr_file_ids),
            "ocr_exclusions_not_present_in_raw": list(missing_reported_ids),
            "quarantined_source_count": len(quarantined_sources),
            "quarantined_sources": [
                {"file_id": file_id, "reason": reason}
                for file_id, reason in sorted(quarantined_sources.items())
            ],
            "geometry_disagreement_count": len(geometry_disagreements),
            "geometry_disagreements": [
                {"file_id": file_id, "block_id": block_id, "reason": reason}
                for file_id, block_id, reason in sorted(geometry_disagreements)
            ],
            "raw_input_sha256": _aggregate_input_hash(raw_paths),
            "ocr_exclusion_list_sha256": _sha256(ocr_needed_path),
            "git_hash": _git_hash(),
            "outputs": {
                path.name: _sha256(path)
                for path in (documents_path, nodes_path, contexts_path, relations_path)
            },
        }
        manifest_path = staging_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _publish_build(staging_dir, output_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return CorpusBuildResult(
        output_dir=output_dir,
        source_document_count=len(source_documents),
        node_count=node_count,
        context_count=context_count,
        lifecycle_relation_count=len(relations),
        audit=audit,
        skipped_ocr_file_ids=reported_ocr_file_ids,
        quarantined_sources=tuple(sorted(quarantined_sources.items())),
        geometry_disagreements=tuple(sorted(geometry_disagreements)),
        manifest_path=output_dir / "manifest.json",
    )


def cmd_build(args: argparse.Namespace) -> None:
    result = build_corpus(
        raw_dir=Path(args.raw_dir),
        output_dir=Path(args.output_dir),
        ocr_needed_path=Path(args.ocr_needed),
    )
    print(
        json.dumps(
            {
                "output_dir": result.output_dir.as_posix(),
                "source_documents": result.source_document_count,
                "nodes": result.node_count,
                "contexts": result.context_count,
                "lifecycle_relations": result.lifecycle_relation_count,
                "skipped_ocr_count": len(result.skipped_ocr_file_ids),
                "quarantined_source_count": len(result.quarantined_sources),
                "manifest": result.manifest_path.as_posix(),
            },
            ensure_ascii=False,
        )
    )
