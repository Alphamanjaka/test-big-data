#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watermark.py — empreinte d'ingestion par table (anti-retraitement).

Fichier runtime : provision/metadata/watermark.json (jamais versionné).

L'extraction RAW peut sauter les sources inchangées grâce à une empreinte du
fichier d'entrée : si la signature de la table est identique à la précédente,
la table n'est ni relue ni ré-écrite sur HDFS. L'état est conservé par
(source, table), avec l'historique des lots et les métadonnées du dernier lot
(colonnes, échantillon, chemin HDFS) pour reconstruire un rapport complet.

Dépendances : stdlib uniquement (fraction importable hors Spark pour les tests).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))
DEFAULT_WATERMARK_PATH = os.path.join(
    PROJECT_ROOT, "provision", "metadata", "watermark.json"
)


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def watermark_path() -> str:
    return os.environ.get("PIPELINE_WATERMARK_PATH") or DEFAULT_WATERMARK_PATH


def load(path: str = None) -> Dict[str, Any]:
    path = path or watermark_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(watermark: Dict[str, Any], path: str = None) -> str:
    path = path or watermark_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(watermark, f, indent=2, ensure_ascii=False)
    return path


def file_signature(file_path: str, chunk_size: int = 65536) -> Dict[str, Any]:
    """Signature d'un fichier : sha256 du contenu, taille et mtime."""
    size = os.path.getsize(file_path)
    mtime = os.path.getmtime(file_path)
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return {"signature": h.hexdigest(), "size": size, "mtime": mtime}


def should_extract(
    watermark: Dict[str, Any],
    source: str,
    table: str,
    sig: Dict[str, Any],
    env_mode: str = None,
    config_mode: str = None,
) -> Tuple[bool, str]:
    """Décide si une table source doit être ré-extraite.

    Priorités : mode config de la source (`full` force toujours) > mode pipeline
    (`full`/`since` forcent) > comparaison d'empreinte avec le watermark.
    """
    cfg = (config_mode or "signature").lower()
    if cfg == "full":
        return True, "config:full"

    env = (env_mode or "full").lower()
    if env in ("full", "since"):
        return True, "pipeline:%s" % env

    entry = watermark.get(source, {}).get(table, {})
    last = entry.get("last") or {}
    if not last.get("signature"):
        return True, "initial"
    if last.get("signature") == sig.get("signature"):
        return False, "unchanged"
    return True, "changed"


def remember(
    watermark: Dict[str, Any],
    source: str,
    table: str,
    sig: Dict[str, Any],
    row_count: int = None,
    columns: Optional[list] = None,
    sample_data: Optional[list] = None,
    hdfs_path: str = None,
    batch_id: str = None,
) -> None:
    """Mémorise un lot extrait : met à jour `last` et ajoute dans `batches`."""
    entry = watermark.setdefault(source, {}).setdefault(table, {})
    extracted_at = _now_iso()
    entry["last"] = {
        "signature": sig.get("signature"),
        "size": sig.get("size"),
        "mtime": sig.get("mtime"),
        "row_count": row_count,
        "extracted_at": extracted_at,
        "hdfs_path": hdfs_path,
    }
    batch = {
        "batch_id": batch_id or extracted_at,
        "signature": sig.get("signature"),
        "size": sig.get("size"),
        "row_count": row_count,
        "extracted_at": extracted_at,
    }
    batches = entry.setdefault("batches", [])
    batches.append(batch)
    if columns is not None:
        entry["columns"] = columns
    if sample_data is not None:
        entry["sample_data"] = sample_data
    if len(batches) > 50:
        entry["batches"] = batches[-50:]


def report_from_watermark(
    watermark: Dict[str, Any], source: str, table: str
) -> Optional[Dict[str, Any]]:
    """Reconstruit une entrée de rapport d'extraction pour une table sautée."""
    entry = watermark.get(source, {}).get(table, {})
    last = entry.get("last") or {}
    if not last.get("signature"):
        return None
    return {
        "source_name": source,
        "table_name": table,
        "table_type": "BASE TABLE",
        "columns": entry.get("columns") or [],
        "row_count": last.get("row_count"),
        "sample_data": entry.get("sample_data") or [],
        "hdfs_path": last.get("hdfs_path"),
        "skipped": True,
        "signature": last.get("signature"),
        "last_extracted_at": last.get("extracted_at"),
    }


def source_summary(watermark: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Résumé lisible d'une source pour l'API /pipeline/status."""
    src = watermark.get(source, {})
    table_count = len(src)
    last_extracted_at = None
    for entry in src.values():
        ts = (entry.get("last") or {}).get("extracted_at")
        if ts and (last_extracted_at is None or ts > last_extracted_at):
            last_extracted_at = ts
    return {"tables": table_count, "last_extracted_at": last_extracted_at}