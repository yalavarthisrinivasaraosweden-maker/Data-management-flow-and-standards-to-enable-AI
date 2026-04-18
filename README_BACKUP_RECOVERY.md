# Data Backup and Recovery

Implements backup and recovery capabilities for database and files, with verification and lifecycle management.

## Features

- On-demand PostgreSQL backup (`pg_dump` + gzip)
- Optional filesystem backup (`zip`)
- Backup metadata registry (`backups/backup_metadata.json`)
- Integrity verification using SHA-256 checksums
- Database restore (`psql`) and file restore (archive extract)
- Backup deletion and retention cleanup endpoints
- RBAC protected endpoints (admin/analyst)

## Endpoints

- `POST /api/v1/backup/create`
- `GET /api/v1/backup/list`
- `GET /api/v1/backup/verify/{backup_id}`
- `POST /api/v1/backup/restore`
- `DELETE /api/v1/backup/delete/{backup_id}`
- `POST /api/v1/backup/cleanup`

## Create Backup Example

```json
{
  "backup_type": "postgres",
  "include_files": true,
  "notes": "Pre-release backup"
}
```

## Restore Example

```json
{
  "backup_id": "backup_20260218_120102",
  "restore_type": "postgres"
}
```

## Requirements

- PostgreSQL client tools installed and on PATH:
  - `pg_dump`
  - `psql`
- Valid `DATABASE_URL` environment variable

## Notes

- All backup endpoints require authenticated RBAC roles.
- Keep backup artifacts outside the app directory in production.
- Use encrypted storage + secure key management for compliance environments.
