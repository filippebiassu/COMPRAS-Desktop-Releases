from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ALLOWED_EXTENSIONS = {".docx"}


def build_manifest(models_root: Path) -> dict:
    entries = []
    seen = set()
    for metadata_path in sorted(models_root.rglob("*.json")):
        if metadata_path.name in {"manifest.json", "deleted.json"}:
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        filename = metadata_path.with_suffix(".docx")
        model_id = str(metadata.get("id", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", model_id) or model_id in seen:
            raise ValueError(f"ID de modelo invalido ou duplicado: {model_id!r}")
        if not filename.is_file() or filename.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(f"DOCX ausente para metadados {metadata_path}")
        if filename.name != metadata_path.with_suffix(".docx").name:
            raise ValueError(f"Nome de DOCX invalido: {filename}")
        seen.add(model_id)
        entries.append({
            "id": model_id,
            "name": str(metadata.get("name") or filename.stem)[:120],
            "category": str(metadata.get("category") or "Outros")[:80],
            "description": str(metadata.get("description") or "")[:300],
            "version": str(metadata.get("version") or "1"),
            "file": filename.relative_to(models_root).as_posix(),
            "sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
        })
    deleted_path = models_root / "deleted.json"
    deleted = json.loads(deleted_path.read_text(encoding="utf-8-sig")) if deleted_path.exists() else []
    if not isinstance(deleted, list) or not all(isinstance(i, str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", i) for i in deleted):
        raise ValueError("models/deleted.json deve ser uma lista de IDs validos.")
    return {
        "schema_version": 1,
        "catalog_version": str(max((entry["version"] for entry in entries), default="1")),
        "base_url": "https://raw.githubusercontent.com/filippebiassu/COMPRAS-Desktop-Releases/main/models/",
        "models": entries,
        "deleted_models": sorted(set(deleted)),
    }


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "models")
    output = root / "manifest.json"
    manifest = build_manifest(root)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifesto criado: {output} ({len(manifest['models'])} modelos)")


if __name__ == "__main__":
    main()
