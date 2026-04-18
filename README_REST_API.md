# RESTful API Documentation

Comprehensive RESTful API for AM Experimental Data Management.

## Base URL

```
http://localhost:8000/api/v1
```

## API Versioning

- Current Version: `v1`
- All endpoints are prefixed with `/api/v1`
- Version is included in the URL path for future compatibility

## Authentication

Currently, the API is open. For production, implement authentication using:
- API Keys
- OAuth 2.0
- JWT Tokens

## Rate Limiting

- Default: 100 requests per minute per IP
- Configure in production based on your needs

## HTTP Methods

- `GET` - Retrieve resources
- `POST` - Create new resources
- `PUT` - Update existing resources (full update)
- `PATCH` - Partial update (not implemented, use PUT)
- `DELETE` - Delete resources

## HTTP Status Codes

- `200 OK` - Successful GET, PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unavailable

## Response Format

### Success Response
```json
{
  "experiment_id": "EXP-2024-001",
  "experiment_name": "PLA Test",
  ...
}
```

### Error Response
```json
{
  "error": "Experiment not found",
  "detail": "Experiment with ID 'EXP-2024-001' not found",
  "status_code": 404,
  "path": "/api/v1/experiments/EXP-2024-001"
}
```

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

## Endpoints

### Root & Health

#### GET `/`
Get API information
```bash
curl http://localhost:8000/
```

Response:
```json
{
  "name": "AM Experimental Data Management API",
  "version": "1.0.0",
  "api_version": "v1",
  "docs": "/api/v1/docs",
  "status": "operational"
}
```

#### GET `/api/v1/health`
Health check endpoint
```bash
curl http://localhost:8000/api/v1/health
```

### Experiments

#### POST `/api/v1/experiments`
Create a new experiment

**Request Body:**
```json
{
  "experiment_id": "EXP-2024-001",
  "experiment_name": "PLA High Speed Test",
  "material_type": "PLA",
  "material_batch": "BATCH-2024-01",
  "build_platform": "Ender 3 Pro",
  "build_date": "2024-01-15T10:00:00",
  "operator": "John Doe",
  "status": "completed",
  "notes": "Initial test",
  "process_parameters": {
    "layer_height": 0.2,
    "print_speed": 80.0,
    "nozzle_temperature": 210.0,
    "bed_temperature": 60.0,
    "infill_percentage": 20.0
  },
  "geometry_data": {
    "part_name": "Test Cube",
    "volume_mm3": 1000.0,
    "surface_area_mm2": 600.0
  },
  "quality_metrics": {
    "tensile_strength_mpa": 45.2,
    "surface_roughness_um": 8.5,
    "porosity_percent": 2.1
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d @experiment.json
```

#### GET `/api/v1/experiments`
List experiments with filtering and pagination

**Query Parameters:**
- `material_type` (optional) - Filter by material type
- `status` (optional) - Filter by status
- `operator` (optional) - Filter by operator
- `build_platform` (optional) - Filter by build platform
- `date_from` (optional) - Filter from date (ISO format)
- `date_to` (optional) - Filter to date (ISO format)
- `sort_by` (optional) - Field to sort by (default: "build_date")
- `sort_order` (optional) - Sort order: "asc" or "desc" (default: "desc")
- `page` (optional) - Page number (default: 1)
- `page_size` (optional) - Items per page (default: 20, max: 100)

**Example:**
```bash
# Get all experiments
curl http://localhost:8000/api/v1/experiments

# Filter by material type
curl "http://localhost:8000/api/v1/experiments?material_type=PLA"

# Paginated results
curl "http://localhost:8000/api/v1/experiments?page=1&page_size=10"

# Filtered and sorted
curl "http://localhost:8000/api/v1/experiments?material_type=PLA&status=completed&sort_by=build_date&sort_order=desc"
```

#### GET `/api/v1/experiments/{experiment_id}`
Get a specific experiment by ID

**Example:**
```bash
curl http://localhost:8000/api/v1/experiments/EXP-2024-001
```

#### PUT `/api/v1/experiments/{experiment_id}`
Update an experiment (partial update supported)

**Request Body:** (only include fields to update)
```json
{
  "status": "completed",
  "notes": "Updated notes",
  "quality_metrics": {
    "tensile_strength_mpa": 46.5
  }
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/experiments/EXP-2024-001 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "notes": "Updated"}'
```

#### DELETE `/api/v1/experiments/{experiment_id}`
Delete an experiment

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/experiments/EXP-2024-001
```

### Process Parameters

#### GET `/api/v1/experiments/{experiment_id}/process-parameters`
Get process parameters for an experiment

**Example:**
```bash
curl http://localhost:8000/api/v1/experiments/EXP-2024-001/process-parameters
```

### Quality Metrics

#### GET `/api/v1/experiments/{experiment_id}/quality-metrics`
Get quality metrics for an experiment

**Example:**
```bash
curl http://localhost:8000/api/v1/experiments/EXP-2024-001/quality-metrics
```

### ML Features

#### GET `/api/v1/experiments/{experiment_id}/ml-features`
Get ML-ready features for an experiment

**Example:**
```bash
curl http://localhost:8000/api/v1/experiments/EXP-2024-001/ml-features
```

Response:
```json
{
  "experiment_id": "EXP-2024-001",
  "features": {
    "layer_height": 0.2,
    "print_speed": 80.0,
    "nozzle_temp": 210.0,
    "tensile_strength": 45.2
  },
  "categories": {
    "layer_height": "process",
    "print_speed": "process",
    "nozzle_temp": "process",
    "tensile_strength": "quality"
  },
  "count": 4
}
```

### Analytics

#### GET `/api/v1/analytics/summary`
Get analytics summary

**Example:**
```bash
curl http://localhost:8000/api/v1/analytics/summary
```

Response:
```json
{
  "total_experiments": 100,
  "material_distribution": {
    "PLA": 50,
    "ABS": 30,
    "PETG": 20
  },
  "average_quality_metrics": {
    "tensile_strength_mpa": 45.2,
    "surface_roughness_um": 8.5,
    "porosity_percent": 2.1
  },
  "process_parameter_ranges": {
    "nozzle_temperature": {
      "min": 200.0,
      "max": 250.0,
      "avg": 220.0
    },
    "print_speed": {
      "min": 50.0,
      "max": 100.0,
      "avg": 75.0
    }
  }
}
```

### Export

#### GET `/api/v1/export/dataset`
Export dataset in various formats

**Query Parameters:**
- `format` (required) - Export format: "csv", "parquet", or "json" (default: "csv")
- `material_type` (optional) - Filter by material type

**Example:**
```bash
# Export as CSV
curl -O http://localhost:8000/api/v1/export/dataset?format=csv

# Export as JSON
curl http://localhost:8000/api/v1/export/dataset?format=json

# Export filtered data
curl -O "http://localhost:8000/api/v1/export/dataset?format=csv&material_type=PLA"
```

## Using the Python Client

A Python client is provided in `api_client_examples.py`:

```python
from api_client_examples import AMDataAPIClient

# Initialize client
client = AMDataAPIClient(base_url="http://localhost:8000")

# Create experiment
experiment = client.create_experiment({
    "experiment_id": "EXP-2024-001",
    "experiment_name": "Test",
    "material_type": "PLA",
    ...
})

# List experiments
experiments = client.list_experiments(material_type="PLA", page=1, page_size=20)

# Get experiment
exp = client.get_experiment("EXP-2024-001")

# Update experiment
updated = client.update_experiment("EXP-2024-001", {"status": "completed"})

# Delete experiment
client.delete_experiment("EXP-2024-001")

# Export data
csv_data = client.export_dataset(format="csv", save_path="data.csv")
```

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Best Practices

1. **Use Pagination**: Always use pagination for list endpoints
2. **Filter Early**: Apply filters to reduce data transfer
3. **Handle Errors**: Check HTTP status codes and error responses
4. **Use Appropriate Methods**: Use GET for retrieval, POST for creation, PUT for updates, DELETE for deletion
5. **Validate Data**: Ensure request data matches the schema
6. **Cache Responses**: Cache GET responses when appropriate
7. **Rate Limiting**: Respect rate limits in production

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "status_code": 404,
  "path": "/api/v1/experiments/INVALID-ID"
}
```

Common error scenarios:
- **400 Bad Request**: Invalid request parameters or data
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource already exists (for POST)
- **500 Internal Server Error**: Server-side error

## Rate Limiting

Rate limits are applied per IP address:
- **Default**: 100 requests per minute
- **Burst**: Up to 20 requests per second

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## CORS

CORS is enabled for all origins. Configure appropriately for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Testing

Test the API using curl, Postman, or the provided Python client:

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test creating an experiment
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "TEST-001",
    "experiment_name": "Test Experiment",
    "material_type": "PLA",
    "status": "completed"
  }'

# Test listing experiments
curl http://localhost:8000/api/v1/experiments
```

## Production Considerations

1. **Authentication**: Implement API key or OAuth authentication
2. **HTTPS**: Use HTTPS in production
3. **Rate Limiting**: Configure appropriate rate limits
4. **CORS**: Restrict CORS to specific domains
5. **Logging**: Implement comprehensive logging
6. **Monitoring**: Set up monitoring and alerting
7. **Backup**: Regular database backups
8. **Documentation**: Keep API documentation updated

## Support

For issues or questions:
- Check the OpenAPI documentation at `/api/v1/docs`
- Review error messages for details
- Check server logs for debugging information
