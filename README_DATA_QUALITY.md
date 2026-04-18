# Data Cleaning and Preprocessing Pipeline Documentation

Comprehensive data quality assurance system for AM experimental data.

## Overview

The data quality pipeline provides:
- **Data Validation**: Rule-based validation of experiment data
- **Data Cleaning**: Outlier detection, missing value handling, duplicate removal
- **Data Preprocessing**: Normalization, feature engineering, correlation removal
- **Quality Reporting**: Comprehensive quality assessment and recommendations
- **Automated Checks**: Continuous quality monitoring

## Features

### 1. Data Validation

**Validation Rules:**
- Range validation for numeric fields
- Type checking
- Required field validation
- Cross-field validation (e.g., temperature relationships)
- Custom validation rules

**Validation Levels:**
- **Strict**: All violations are errors
- **Moderate**: Some violations are warnings (default)
- **Lenient**: Most violations are warnings

**Example Validation Rules:**
```python
- layer_height: 0.05 - 0.5 mm
- print_speed: 10 - 300 mm/s
- nozzle_temperature: 150 - 350 °C
- tensile_strength_mpa: 0 - 500 MPa
- surface_roughness_um: 0 - 100 μm
```

### 2. Data Cleaning

**Outlier Detection:**
- IQR method (Interquartile Range)
- Z-score method
- Configurable thresholds

**Missing Value Handling:**
- Mean imputation
- Median imputation
- Mode imputation
- KNN imputation
- Custom strategies

**Duplicate Removal:**
- Identify duplicate records
- Configurable duplicate detection criteria
- Preserve first occurrence

### 3. Data Preprocessing

**Normalization:**
- Standard scaling (Z-score)
- Min-Max scaling
- Robust scaling

**Feature Engineering:**
- Temperature difference (nozzle - bed)
- Surface area to volume ratio
- Aspect ratios
- Custom derived features

**Correlation Removal:**
- Identify highly correlated features
- Remove redundant features
- Configurable threshold

### 4. Quality Reporting

**Quality Metrics:**
- Completeness score (0-1)
- Validity score (0-1)
- Consistency score (0-1)
- Overall quality score

**Issue Tracking:**
- Error severity issues
- Warning severity issues
- Info severity issues
- Detailed issue descriptions

**Recommendations:**
- Actionable recommendations
- Priority-based suggestions
- Field-specific guidance

## API Endpoints

### Validate Experiments

```http
POST /api/v1/data-quality/validate
```

**Request Body:**
```json
{
  "experiment_id": "EXP-2024-001",
  "validation_level": "moderate",
  "experiments": [...]  // Optional: validate multiple experiments
}
```

**Response:**
```json
{
  "experiment_id": "EXP-2024-001",
  "timestamp": "2024-01-15T10:00:00",
  "total_records": 1,
  "valid_records": 1,
  "invalid_records": 0,
  "completeness_score": 0.85,
  "validity_score": 1.0,
  "consistency_score": 0.95,
  "overall_score": 0.93,
  "issues": [...],
  "statistics": {...},
  "recommendations": [...]
}
```

### Clean Dataset

```http
POST /api/v1/data-quality/clean
```

**Request Body:**
```json
{
  "experiment_ids": ["EXP-2024-001", "EXP-2024-002"],
  "remove_outliers": true,
  "handle_missing": true,
  "remove_duplicates": true,
  "normalize": false
}
```

**Query Parameters:**
- `material_type` - Filter by material type

**Response:**
```json
{
  "cleaned_data": [...],
  "cleaning_log": {
    "initial_rows": 100,
    "final_rows": 95,
    "rows_removed": 5,
    "steps": [
      {"step": "remove_duplicates", "removed": 2},
      {"step": "handle_missing", "filled": 10},
      {"step": "remove_outliers", "removed": 3}
    ]
  },
  "statistics": {
    "initial_rows": 100,
    "final_rows": 95,
    "removed_rows": 5
  }
}
```

### Preprocess Dataset

```http
POST /api/v1/data-quality/preprocess
```

**Request Body:**
```json
{
  "experiment_ids": ["EXP-2024-001"],
  "normalize": true,
  "normalize_method": "standard",
  "feature_engineering": true,
  "remove_correlated": false,
  "correlation_threshold": 0.95
}
```

**Response:**
```json
{
  "preprocessed_data": [...],
  "preprocessing_info": {
    "normalized": true,
    "feature_engineering": true,
    "removed_correlated": false,
    "final_features": ["layer_height", "print_speed", ...]
  }
}
```

### Get Quality Issues

```http
GET /api/v1/data-quality/issues?experiment_id=EXP-2024-001&severity=error
```

**Query Parameters:**
- `experiment_id` - Filter by experiment
- `material_type` - Filter by material
- `severity` - Filter by severity (error, warning, info)

**Response:**
```json
{
  "total_issues": 5,
  "issues": [
    {
      "issue_type": "out_of_range",
      "field": "process_parameters.nozzle_temperature",
      "severity": "error",
      "message": "Value 400 is above maximum 350",
      "value": 400,
      "expected_range": {"min": 150, "max": 350},
      "suggestion": "Value should be between 150 and 350"
    }
  ]
}
```

## Usage Examples

### Python Client

```python
from data_quality_client import DataQualityClient

client = DataQualityClient()

# Validate experiment
report = client.validate_experiment(
    experiment_id="EXP-2024-001",
    validation_level="moderate"
)
print(f"Quality Score: {report['overall_score']:.2%}")

# Clean dataset
cleaned = client.clean_dataset(
    material_type="PLA",
    remove_outliers=True,
    handle_missing=True
)

# Preprocess for ML
preprocessed = client.preprocess_dataset(
    material_type="PLA",
    normalize=True,
    feature_engineering=True
)

# Get issues
issues = client.get_quality_issues(severity="error")
```

### cURL Examples

```bash
# Validate experiment
curl -X POST http://localhost:8000/api/v1/data-quality/validate \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "EXP-2024-001",
    "validation_level": "moderate"
  }'

# Clean dataset
curl -X POST http://localhost:8000/api/v1/data-quality/clean \
  -H "Content-Type: application/json" \
  -d '{
    "remove_outliers": true,
    "handle_missing": true,
    "remove_duplicates": true
  }'

# Preprocess dataset
curl -X POST http://localhost:8000/api/v1/data-quality/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "normalize": true,
    "feature_engineering": true
  }'
```

## Validation Rules

### Process Parameters
- `layer_height`: 0.05 - 0.5 mm
- `print_speed`: 10 - 300 mm/s
- `nozzle_temperature`: 150 - 350 °C
- `bed_temperature`: 0 - 150 °C
- `infill_percentage`: 0 - 100%

### Quality Metrics
- `tensile_strength_mpa`: 0 - 500 MPa
- `surface_roughness_um`: 0 - 100 μm
- `porosity_percent`: 0 - 100%
- `density_g_per_cm3`: 0.5 - 3.0 g/cm³

### Cross-Field Validation
- Nozzle temperature should be > bed temperature
- Volume should be consistent with bounding box
- Process parameters should be consistent with material type

## Cleaning Strategies

### Outlier Detection
- **IQR Method**: Uses interquartile range (default)
- **Z-Score Method**: Uses standard deviations

### Missing Value Handling
- **Mean**: Replace with column mean
- **Median**: Replace with column median
- **Mode**: Replace with most frequent value
- **KNN**: Use k-nearest neighbors imputation

### Normalization Methods
- **Standard**: Z-score normalization (mean=0, std=1)
- **MinMax**: Scale to [0, 1] range
- **Robust**: Use median and IQR (robust to outliers)

## Quality Scores

### Completeness Score
Measures how many fields have values:
```
Completeness = (Filled Fields / Total Fields) × 100%
```

### Validity Score
Measures how many records pass validation:
```
Validity = (Valid Records / Total Records) × 100%
```

### Consistency Score
Measures internal consistency:
```
Consistency = (Consistent Checks / Total Checks) × 100%
```

### Overall Score
Average of all scores:
```
Overall = (Completeness + Validity + Consistency) / 3
```

## Best Practices

1. **Validate Before Cleaning**: Always validate data before cleaning
2. **Use Appropriate Validation Level**: Choose strict/moderate/lenient based on use case
3. **Review Quality Reports**: Check quality reports before ML training
4. **Handle Missing Values Carefully**: Choose imputation strategy based on data characteristics
5. **Document Cleaning Steps**: Keep track of all cleaning operations
6. **Preserve Original Data**: Always keep original data before cleaning
7. **Test Cleaning Impact**: Compare results before and after cleaning

## Integration

### With Main API
```python
# Auto-validate on create/update
@app.post("/api/v1/experiments")
def create_experiment(...):
    # ... create experiment ...
    
    # Validate
    pipeline = DataQualityPipeline()
    issues = pipeline.validate_experiment(experiment_data)
    
    if any(i.severity == "error" for i in issues):
        raise HTTPException(400, "Data validation failed")
```

### With ML Pipeline
```python
# Preprocess before training
preprocessed = client.preprocess_dataset(
    material_type="PLA",
    normalize=True,
    feature_engineering=True
)

# Use preprocessed data for training
train_model(preprocessed['preprocessed_data'])
```

## Performance

- **Validation**: O(n) where n is number of experiments
- **Cleaning**: O(n log n) for duplicate removal, O(n) for other operations
- **Preprocessing**: O(n) for normalization, O(n²) for correlation analysis

## Limitations

- Large datasets may require batch processing
- Some cleaning operations are memory-intensive
- Correlation analysis can be slow for many features

## Future Enhancements

- [ ] Automated anomaly detection
- [ ] Real-time quality monitoring
- [ ] Custom validation rule builder
- [ ] Quality score thresholds and alerts
- [ ] Integration with version control
- [ ] Quality dashboard visualization
- [ ] Automated data repair suggestions

## Troubleshooting

### Validation Fails
- Check validation rules
- Review data ranges
- Adjust validation level

### Cleaning Removes Too Much Data
- Adjust outlier detection thresholds
- Review cleaning options
- Check for data entry errors

### Preprocessing Issues
- Verify numeric columns
- Check for infinite values
- Ensure sufficient data points

## Support

For issues or questions:
- Check API documentation at `/api/v1/docs`
- Review quality reports for details
- Check server logs for errors
