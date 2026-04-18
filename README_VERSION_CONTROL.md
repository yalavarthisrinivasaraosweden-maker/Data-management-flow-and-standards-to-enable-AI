# Version Control System Documentation

Comprehensive version control system for tracking and managing changes to AM experimental data.

## Overview

The version control system provides:
- **Change Tracking**: Automatic tracking of all data changes
- **Version History**: Complete history of all versions
- **Version Comparison**: Compare any two versions
- **Rollback**: Restore to any previous version
- **Tagging**: Organize versions with tags
- **Audit Trail**: Track who made changes and when

## Features

### 1. Version Snapshots
- Automatic creation of version snapshots
- Full data capture including all related tables
- Hash-based duplicate detection
- Efficient storage using JSON

### 2. Version History
- Complete chronological history
- Track creator, timestamp, and change description
- Identify current version
- Filter and search capabilities

### 3. Version Comparison
- Compare any two versions
- Identify changed, added, and removed fields
- Detailed diff information
- Visual comparison support

### 4. Version Restoration
- Restore to any previous version
- Automatic version creation on restore
- Maintains complete audit trail
- Safe rollback operations

### 5. Tagging System
- Add custom tags to versions
- Filter versions by tags
- Organize versions for easy access
- Multiple tags per version

## Database Schema

### DataVersion Table
```sql
- version_id (PK)
- experiment_id (FK)
- version_number
- version_hash
- created_by
- created_at
- change_description
- change_type
- experiment_snapshot (JSON)
- process_parameters_snapshot (JSON)
- geometry_data_snapshot (JSON)
- quality_metrics_snapshot (JSON)
- changed_fields (JSON)
- previous_version_id (FK)
- tags (JSON)
- is_current (Boolean)
```

### VersionTag Table
```sql
- tag_id (PK)
- version_id (FK)
- tag_name
- tag_value
- created_at
```

## API Endpoints

### Create Version
```http
POST /api/v1/experiments/{experiment_id}/versions
```

**Request Body:**
```json
{
  "created_by": "user@example.com",
  "change_type": "update",
  "change_description": "Updated quality metrics",
  "tags": ["reviewed", "validated"]
}
```

**Response:**
```json
{
  "version_id": 1,
  "experiment_id": "EXP-2024-001",
  "version_number": 1,
  "version_hash": "abc123...",
  "created_by": "user@example.com",
  "created_at": "2024-01-15T10:00:00",
  "change_description": "Updated quality metrics",
  "change_type": "update",
  "changed_fields": ["quality_metrics.tensile_strength_mpa"],
  "tags": ["reviewed", "validated"],
  "is_current": true
}
```

### Get Version History
```http
GET /api/v1/experiments/{experiment_id}/versions
```

**Response:**
```json
{
  "experiment_id": "EXP-2024-001",
  "total_versions": 5,
  "current_version": 5,
  "versions": [
    {
      "version_id": 5,
      "version_number": 5,
      "created_by": "user@example.com",
      "created_at": "2024-01-20T10:00:00",
      "change_type": "update",
      "is_current": true
    },
    ...
  ]
}
```

### Get Version Snapshot
```http
GET /api/v1/versions/{version_id}
```

**Response:**
```json
{
  "version_id": 1,
  "experiment_id": "EXP-2024-001",
  "version_number": 1,
  "created_at": "2024-01-15T10:00:00",
  "created_by": "user@example.com",
  "experiment": {
    "experiment_id": "EXP-2024-001",
    "experiment_name": "PLA Test",
    ...
  },
  "process_parameters": {...},
  "geometry_data": {...},
  "quality_metrics": {...}
}
```

### Restore Version
```http
POST /api/v1/versions/{version_id}/restore
```

**Request Body:**
```json
{
  "restored_by": "admin@example.com",
  "create_new_version": true
}
```

**Response:**
```json
{
  "message": "Experiment restored to version 3",
  "experiment_id": "EXP-2024-001",
  "restored_by": "admin@example.com",
  "restored_at": "2024-01-21T10:00:00"
}
```

### Compare Versions
```http
GET /api/v1/versions/{version1_id}/compare/{version2_id}
```

**Response:**
```json
{
  "version1_id": 1,
  "version2_id": 2,
  "experiment_id": "EXP-2024-001",
  "differences": {
    "quality_metrics.tensile_strength_mpa": {
      "old_value": 45.2,
      "new_value": 46.5
    }
  },
  "added_fields": [],
  "removed_fields": [],
  "modified_fields": ["quality_metrics.tensile_strength_mpa"]
}
```

### List All Versions
```http
GET /api/v1/versions?experiment_id=EXP-2024-001&limit=10&offset=0
```

**Query Parameters:**
- `experiment_id` - Filter by experiment
- `created_by` - Filter by creator
- `change_type` - Filter by change type
- `tag` - Filter by tag
- `limit` - Maximum results
- `offset` - Pagination offset

### Add Tag
```http
POST /api/v1/versions/{version_id}/tags
```

**Request Body:**
```json
{
  "tag_name": "production-ready",
  "tag_value": "true"
}
```

### Remove Tag
```http
DELETE /api/v1/versions/{version_id}/tags/{tag_name}
```

## Usage Examples

### Python Client

```python
from version_control_client import VersionControlClient

client = VersionControlClient()

# Create a version snapshot
version = client.create_version(
    experiment_id="EXP-2024-001",
    created_by="john.doe@example.com",
    change_type="update",
    change_description="Updated measurements",
    tags=["reviewed"]
)

# Get version history
history = client.get_version_history("EXP-2024-001")

# Compare versions
diff = client.compare_versions(version1_id=1, version2_id=2)

# Restore to previous version
result = client.restore_version(
    version_id=3,
    restored_by="admin@example.com"
)
```

### cURL Examples

```bash
# Create version
curl -X POST http://localhost:8000/api/v1/experiments/EXP-2024-001/versions \
  -H "Content-Type: application/json" \
  -d '{
    "created_by": "user@example.com",
    "change_type": "update",
    "change_description": "Updated quality metrics"
  }'

# Get version history
curl http://localhost:8000/api/v1/experiments/EXP-2024-001/versions

# Compare versions
curl http://localhost:8000/api/v1/versions/1/compare/2

# Restore version
curl -X POST http://localhost:8000/api/v1/versions/3/restore \
  -H "Content-Type: application/json" \
  -d '{"restored_by": "admin@example.com"}'
```

## Change Types

- **create**: Initial creation of experiment
- **update**: Modification of experiment data
- **delete**: Deletion of experiment (snapshot before deletion)
- **restore**: Restoration to a previous version

## Best Practices

1. **Create Versions Before Major Changes**: Always create a version before making significant updates
2. **Use Descriptive Change Descriptions**: Clearly describe what changed and why
3. **Tag Important Versions**: Use tags to mark production-ready or validated versions
4. **Regular Versioning**: Create versions at regular intervals or after each significant change
5. **Review Before Restore**: Always review version differences before restoring
6. **Document Changes**: Include detailed change descriptions for audit purposes

## Integration with Main API

The version control system can be integrated with the main REST API to automatically create versions:

```python
# In update endpoint
@app.put("/api/v1/experiments/{experiment_id}")
def update_experiment(...):
    # ... update logic ...
    
    # Auto-create version
    create_version(
        db=db,
        experiment_id=experiment_id,
        created_by=current_user,
        change_type="update",
        change_description="Experiment updated via API"
    )
```

## Performance Considerations

- **Storage**: Versions are stored as JSON for efficiency
- **Indexing**: Key fields are indexed for fast queries
- **Hash-based Deduplication**: Prevents storing duplicate versions
- **Lazy Loading**: Snapshot data loaded only when needed
- **Pagination**: List endpoints support pagination

## Security

- **Access Control**: Implement user authentication
- **Audit Trail**: All changes tracked with creator information
- **Immutable Versions**: Versions cannot be modified once created
- **Restore Permissions**: Control who can restore versions

## Limitations

- **Storage Growth**: Versions accumulate over time, consider archival
- **Large Snapshots**: Very large experiments may have large snapshots
- **Concurrent Updates**: Handle concurrent updates appropriately
- **Performance**: Many versions may slow queries

## Future Enhancements

- [ ] Automatic version creation on updates
- [ ] Version branching and merging
- [ ] Version export/import
- [ ] Version archiving
- [ ] Visual diff interface
- [ ] Version comments and discussions
- [ ] Version approval workflow
- [ ] Integration with Git-like workflows

## Troubleshooting

### Version Not Created
- Check if data actually changed (hash-based deduplication)
- Verify experiment exists
- Check database permissions

### Restore Failed
- Verify version exists
- Check experiment still exists
- Review database constraints

### Performance Issues
- Use pagination for large version lists
- Add indexes if needed
- Consider archiving old versions

## Support

For issues or questions:
- Check API documentation at `/api/v1/docs`
- Review version history for changes
- Check server logs for errors
