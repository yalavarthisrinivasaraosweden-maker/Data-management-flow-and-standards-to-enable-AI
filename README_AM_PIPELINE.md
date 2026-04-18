# AM Experimental Data Management Pipeline

A comprehensive data management pipeline designed specifically for Additive Manufacturing (AM) experimental data. This system supports efficient storage, easy access, and future use in ML and AI applications.

## Features

### 🗄️ **Efficient Storage**
- **Structured Database Schema**: Optimized SQLite database with normalized tables for:
  - Experiment metadata
  - Process parameters (temperature, speed, infill, etc.)
  - Geometry data (volume, surface area, bounding boxes)
  - Quality metrics (tensile strength, surface roughness, porosity, etc.)
  - Time-series sensor data
  - ML-ready features

- **Indexed Queries**: Database indexes for fast filtering and retrieval
- **Data Versioning**: Track changes to experimental data over time

### 🔍 **Easy Access**
- **RESTful API**: Clean, well-documented API endpoints
- **Interactive Dashboard**: Web-based interface for data visualization and management
- **Flexible Filtering**: Filter experiments by material type, status, date range
- **Export Capabilities**: Export data in multiple formats (CSV, Parquet, JSON)

### 🤖 **ML/AI Ready**
- **Automatic Feature Engineering**: Pre-computed ML features from raw data
- **Standard Formats**: Export datasets in CSV, Parquet, and JSON formats
- **Feature Extraction**: Derived features like temperature differences, aspect ratios, surface-to-volume ratios
- **Structured Data**: Consistent schema for easy integration with ML pipelines

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements_am.txt
```

2. **Start the server:**
```bash
python am_data_pipeline.py
```

Or using uvicorn directly:
```bash
uvicorn am_data_pipeline:app --reload --host 0.0.0.0 --port 8000
```

3. **Access the dashboard:**
Open your browser and navigate to: `http://localhost:8000`

## Database Schema

### Tables

1. **experiments** - Main experiment records
   - experiment_id (Primary Key)
   - experiment_name, material_type, material_batch
   - build_platform, build_date, operator
   - status, notes, timestamps

2. **process_parameters** - AM process settings
   - layer_height, print_speed
   - nozzle_temperature, bed_temperature
   - infill_percentage, infill_pattern
   - shell_count, support settings
   - print_time_hours

3. **geometry_data** - Build geometry information
   - part_name, STL file path
   - volume, surface_area
   - bounding_box dimensions
   - complexity_score, support_volume

4. **quality_metrics** - Measured quality characteristics
   - dimensional_accuracy
   - surface_roughness
   - mechanical properties (tensile, yield strength)
   - density, porosity, hardness
   - defect information

5. **sensor_data** - Time-series sensor readings
   - sensor_type, timestamp
   - value, unit, location

6. **ml_features** - Precomputed ML features
   - feature_name, feature_value
   - feature_category

7. **data_versions** - Data version tracking
   - version_number, change_description
   - changed_fields

## API Endpoints

### Experiments
- `POST /api/experiments` - Create new experiment
- `GET /api/experiments` - List experiments (with optional filtering)
- `GET /api/experiments/{experiment_id}` - Get specific experiment
- `GET /api/experiments/{experiment_id}/ml-features` - Get ML features
- `GET /api/experiments/{experiment_id}/sensor-data` - Get sensor data

### Data Export
- `GET /api/export/ml-dataset` - Export dataset (CSV, Parquet, JSON)
  - Query params: `format` (csv|parquet|json), `material_type` (optional)

### Analytics
- `GET /api/analytics/summary` - Get dataset analytics summary

### Sensor Data
- `POST /api/experiments/{experiment_id}/sensor-data` - Add sensor data point

## Usage Examples

### 1. Adding an Experiment via API

```python
import requests

experiment = {
    "experiment_id": "EXP-2024-001",
    "experiment_name": "PLA High Speed Test",
    "material_type": "PLA",
    "process_parameters": {
        "layer_height": 0.2,
        "print_speed": 80.0,
        "nozzle_temperature": 210.0,
        "bed_temperature": 60.0,
        "infill_percentage": 20.0
    },
    "quality_metrics": {
        "tensile_strength_mpa": 45.2,
        "surface_roughness_um": 8.5,
        "porosity_percent": 2.1
    }
}

response = requests.post("http://localhost:8000/api/experiments", json=experiment)
```

### 2. Exporting ML Dataset

```python
# Export as CSV
response = requests.get("http://localhost:8000/api/export/ml-dataset?format=csv")
with open("am_dataset.csv", "wb") as f:
    f.write(response.content)

# Export as Parquet (better for ML)
response = requests.get("http://localhost:8000/api/export/ml-dataset?format=parquet")
with open("am_dataset.parquet", "wb") as f:
    f.write(response.content)
```

### 3. Using Example Data

```bash
# First, start the server
python am_data_pipeline.py

# In another terminal, run the ingestion script
python example_data_ingestion.py
```

## ML/AI Integration

### Feature Engineering

The pipeline automatically computes ML-ready features:
- **Process Features**: Direct process parameters (temperatures, speeds, etc.)
- **Derived Features**: Temperature differences, ratios
- **Geometry Features**: Surface-to-volume ratios, aspect ratios
- **Quality Features**: Direct quality metrics

### Data Export Formats

1. **CSV**: Human-readable, compatible with most tools
2. **Parquet**: Efficient columnar format, ideal for ML workflows
3. **JSON**: Flexible format for web applications

### Example ML Workflow

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Load exported dataset
df = pd.read_parquet("am_dataset.parquet")

# Prepare features and target
X = df[['nozzle_temperature', 'print_speed', 'infill_percentage', 
        'layer_height', 'volume_mm3']]
y = df['tensile_strength_mpa']

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestRegressor()
model.fit(X_train, y_train)

# Evaluate
score = model.score(X_test, y_test)
print(f"Model R² score: {score}")
```

## Dashboard Features

- **Dashboard Tab**: Overview statistics and material distribution charts
- **Experiments Tab**: Browse and filter experiments
- **Add Experiment Tab**: Form-based data entry
- **Analytics Tab**: Dataset summary and statistics
- **ML Export Tab**: Export datasets in various formats

## Evaluation Metrics

The pipeline tracks:
- Total number of experiments
- Material distribution
- Average quality metrics (tensile strength, surface roughness, porosity)
- Process parameter ranges
- Data completeness statistics

## Project Structure

```
.
├── am_data_pipeline.py      # Main FastAPI backend
├── am_dashboard.html         # Frontend dashboard
├── example_data_ingestion.py # Example data ingestion script
├── requirements_am.txt      # Python dependencies
├── README_AM_PIPELINE.md    # This file
├── am_data.db               # SQLite database (created automatically)
└── am_data_storage/         # Storage directory for files
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Future Enhancements

- [ ] Support for additional AM processes (SLA, SLS, etc.)
- [ ] Real-time sensor data streaming
- [ ] Advanced ML feature engineering
- [ ] Data validation rules and constraints
- [ ] Batch import from CSV/Excel
- [ ] Integration with CAD software
- [ ] Automated quality assessment using ML models
- [ ] Data visualization and plotting capabilities

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
