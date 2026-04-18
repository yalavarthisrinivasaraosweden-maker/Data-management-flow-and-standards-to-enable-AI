"""
Data backup and recovery system for API + database operations.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from restful_api import app
from security_privacy import require_roles


BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
METADATA_FILE = BACKUP_DIR / "backup_metadata.json"


def _load_metadata() -> List[Dict[str, Any]]:
    if not METADATA_FILE.exists():
        return []
    with METADATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_metadata(rows: List[Dict[str, Any]]) -> None:
    with METADATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class BackupCreateRequest(BaseModel):
    backup_type: str = Field("postgres", description="postgres or files")
    include_files: bool = Field(False, description="Include local app files archive")
    notes: Optional[str] = None


class BackupRestoreRequest(BaseModel):
    backup_id: str
    restore_type: str = Field("postgres", description="postgres or files")


def _create_postgres_backup(backup_id: str) -> Dict[str, Any]:
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/am_data_db")
    # Parse url crudely for pg_dump env vars.
    # Format: postgresql://user:pass@host:port/db
    try:
        no_proto = db_url.split("://", 1)[1]
        creds_host, db_name = no_proto.rsplit("/", 1)
        creds, hostport = creds_host.split("@", 1)
        user, password = creds.split(":", 1)
        host, port = hostport.split(":", 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid DATABASE_URL format") from exc

    out_file = BACKUP_DIR / f"{backup_id}.sql.gz"
    dump_cmd = [
        "pg_dump",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-d",
        db_name,
        "--no-owner",
        "--no-privileges",
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    try:
        proc = subprocess.run(dump_cmd, env=env, capture_output=True, check=True)
        with gzip.open(out_file, "wb") as gz:
            gz.write(proc.stdout)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="pg_dump not found. Install PostgreSQL client tools.",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Backup failed: {exc.stderr.decode(errors='ignore')}") from exc

    return {
        "path": str(out_file),
        "size_bytes": out_file.stat().st_size,
        "checksum_sha256": _sha256_file(out_file),
    }


def _create_files_backup(backup_id: str) -> Dict[str, Any]:
    archive_base = BACKUP_DIR / f"{backup_id}_files"
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=str(Path.cwd()))
    p = Path(archive_path)
    return {
        "path": str(p),
        "size_bytes": p.stat().st_size,
        "checksum_sha256": _sha256_file(p),
    }


@app.post("/api/v1/backup/create", tags=["Backup & Recovery"])
def create_backup(
    payload: BackupCreateRequest,
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    backup_id = f"backup_{_timestamp()}"
    artifacts: List[Dict[str, Any]] = []

    if payload.backup_type == "postgres":
        artifacts.append({"type": "postgres", **_create_postgres_backup(backup_id)})
    elif payload.backup_type == "files":
        artifacts.append({"type": "files", **_create_files_backup(backup_id)})
    else:
        raise HTTPException(status_code=400, detail="backup_type must be postgres or files")

    if payload.include_files and payload.backup_type != "files":
        artifacts.append({"type": "files", **_create_files_backup(backup_id)})

    meta = _load_metadata()
    row = {
        "backup_id": backup_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "created_by": user["username"],
        "notes": payload.notes,
        "artifacts": artifacts,
    }
    meta.append(row)
    _save_metadata(meta)
    return row


@app.get("/api/v1/backup/list", tags=["Backup & Recovery"])
def list_backups(
    limit: int = Query(50, ge=1, le=1000),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    del user
    rows = _load_metadata()
    rows = sorted(rows, key=lambda r: r["created_at_utc"], reverse=True)
    return {"count": min(len(rows), limit), "backups": rows[:limit]}


@app.get("/api/v1/backup/verify/{backup_id}", tags=["Backup & Recovery"])
def verify_backup(
    backup_id: str,
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    del user
    rows = _load_metadata()
    match = next((r for r in rows if r["backup_id"] == backup_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Backup not found")

    checks = []
    ok = True
    for art in match["artifacts"]:
        p = Path(art["path"])
        exists = p.exists()
        checksum_ok = False
        if exists:
            checksum_ok = _sha256_file(p) == art["checksum_sha256"]
        checks.append(
            {
                "type": art["type"],
                "path": art["path"],
                "exists": exists,
                "checksum_ok": checksum_ok,
            }
        )
        ok = ok and exists and checksum_ok

    return {"backup_id": backup_id, "valid": ok, "checks": checks}


@app.post("/api/v1/backup/restore", tags=["Backup & Recovery"])
def restore_backup(
    payload: BackupRestoreRequest,
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    rows = _load_metadata()
    match = next((r for r in rows if r["backup_id"] == payload.backup_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Backup not found")

    artifact = next((a for a in match["artifacts"] if a["type"] == payload.restore_type), None)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"No {payload.restore_type} artifact in backup")

    p = Path(artifact["path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="Backup file missing on disk")

    if payload.restore_type == "files":
        restore_dir = BACKUP_DIR / f"restore_{payload.backup_id}_{_timestamp()}"
        restore_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(p), str(restore_dir))
        return {"message": "Files restored", "restore_path": str(restore_dir)}

    # postgres restore
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/am_data_db")
    try:
        no_proto = db_url.split("://", 1)[1]
        creds_host, db_name = no_proto.rsplit("/", 1)
        creds, hostport = creds_host.split("@", 1)
        user_db, password = creds.split(":", 1)
        host, port = hostport.split(":", 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid DATABASE_URL format") from exc

    sql_bytes = gzip.decompress(p.read_bytes())
    restore_cmd = [
        "psql",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user_db,
        "-d",
        db_name,
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    try:
        subprocess.run(restore_cmd, env=env, input=sql_bytes, capture_output=True, check=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="psql not found. Install PostgreSQL client tools.") from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Restore failed: {exc.stderr.decode(errors='ignore')}") from exc

    return {"message": "Database restore completed", "backup_id": payload.backup_id}


@app.delete("/api/v1/backup/delete/{backup_id}", tags=["Backup & Recovery"])
def delete_backup(
    backup_id: str,
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    rows = _load_metadata()
    idx = next((i for i, r in enumerate(rows) if r["backup_id"] == backup_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Backup not found")

    row = rows[idx]
    for art in row["artifacts"]:
        p = Path(art["path"])
        if p.exists():
            p.unlink()
    rows.pop(idx)
    _save_metadata(rows)
    return {"message": "Backup deleted", "backup_id": backup_id}


@app.post("/api/v1/backup/cleanup", tags=["Backup & Recovery"])
def cleanup_backups(
    keep_latest: int = Body(10, embed=True),
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    rows = sorted(_load_metadata(), key=lambda r: r["created_at_utc"], reverse=True)
    if keep_latest < 0:
        raise HTTPException(status_code=400, detail="keep_latest must be >= 0")

    to_delete = rows[keep_latest:]
    kept = rows[:keep_latest]
    deleted_ids = []
    for row in to_delete:
        for art in row["artifacts"]:
            p = Path(art["path"])
            if p.exists():
                p.unlink()
        deleted_ids.append(row["backup_id"])

    _save_metadata(kept)
    return {"deleted_count": len(deleted_ids), "deleted_backup_ids": deleted_ids, "kept_count": len(kept)}
