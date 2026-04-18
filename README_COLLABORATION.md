# Data Sharing and Collaboration System

Implements secure sharing and collaboration for experiments, reports, and datasets.

## Capabilities

- Share links with token-based access and expiration
- Revoke shares and list existing shares
- Collaboration comments per resource
- Invite recording for collaborators
- Activity feed for collaboration events
- RBAC enforcement via existing security module

## Resource Types

- `experiment`
- `report`
- `dataset`

## Endpoints

- `POST /api/v1/collab/share`
- `GET /api/v1/collab/share/resolve/{token}`
- `POST /api/v1/collab/share/revoke/{share_id}`
- `GET /api/v1/collab/share/list`
- `POST /api/v1/collab/comment`
- `GET /api/v1/collab/comments`
- `POST /api/v1/collab/invite`
- `GET /api/v1/collab/activity`

## Create Share Example

```json
{
  "resource_type": "experiment",
  "resource_id": "EXP-2024-001",
  "access_level": "view",
  "expires_in_hours": 72,
  "metadata": {
    "purpose": "peer review"
  }
}
```

## Add Comment Example

```json
{
  "resource_type": "experiment",
  "resource_id": "EXP-2024-001",
  "message": "Please re-check tensile test calibration."
}
```

## Notes

- Non-admin users only see their own created share links.
- Token resolution requires authentication.
- Collaboration actions are logged to activity feed.
