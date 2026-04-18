# Data Analysis and Visualization Pipeline Documentation

Comprehensive data exploration and discovery system for AM experimental data.

## Overview

The data analysis pipeline provides:
- **Statistical Analysis**: Descriptive statistics, distributions, correlations
- **Visualization Generation**: Multiple chart types for data exploration
- **Pattern Discovery**: Clustering, anomaly detection, trend analysis
- **Dimensionality Reduction**: PCA for feature analysis
- **Interactive Exploration**: API-driven data exploration

## Features

### 1. Statistical Analysis

**Descriptive Statistics:**
- Mean, median, standard deviation
- Min, max, quartiles
- Skewness and kurtosis
- Complete statistical summaries

**Correlation Analysis:**
- Pearson correlation matrix
- Strong/weak correlation identification
- Statistical significance testing
- Correlation heatmaps

**Distribution Analysis:**
- Distribution type detection
- Normality testing
- Histogram and KDE plots
- Box plots

### 2. Visualization Generation

**Available Plot Types:**
- **Scatter Plot**: X vs Y with optional color coding
- **Correlation Heatmap**: Correlation matrix visualization
- **Distribution Plot**: Histogram, KDE, or box plot
- **Time Series**: Temporal trends
- **Pair Plot**: Scatter matrix for multiple variables
- **Cluster Visualization**: Visualize clustering results
- **PCA Visualization**: Principal component analysis plots
- **Summary Dashboard**: Multi-panel overview

### 3. Pattern Discovery

**Clustering:**
- K-means clustering
- Cluster visualization
- Cluster characteristics

**Anomaly Detection:**
- Z-score based detection
- Outlier identification
- Anomaly scoring

**Trend Analysis:**
- Linear trend detection
- Significance testing
- Trend visualization

**Relationship Discovery:**
- Correlation identification
- Strong relationship detection
- Pattern recognition

### 4. Dimensionality Reduction

**Principal Component Analysis (PCA):**
- Dimensionality reduction
- Variance explanation
- Component visualization
- Feature contribution analysis

## API Endpoints

### Exploratory Data Analysis

```http
POST /api/v1/analysis/explore
```

**Request Body:**
```json
{
  "experiment_ids": ["EXP-2024-001"],
  "material_type": "PLA",
  "include_visualizations": true
}
```

**Response:**
```json
{
  "report": {
    "statistical_summary": {...},
    "correlation_analysis": {...},
    "distribution_analysis": [...],
    "pattern_discovery": {...},
    "insights": [...],
    "recommendations": [...]
  },
  "visualizations": {
    "correlation_heatmap": {...},
    "summary_dashboard": {...}
  }
}
```

### Create Visualization

```http
POST /api/v1/analysis/visualize
```

**Request Body:**
```json
{
  "plot_type": "scatter",
  "x_column": "nozzle_temperature",
  "y_column": "tensile_strength_mpa",
  "color_by": "infill_percentage",
  "title": "Temperature vs Strength"
}
```

**Query Parameters:**
- `material_type` - Filter by material

**Response:**
```json
{
  "type": "scatter",
  "x": "nozzle_temperature",
  "y": "tensile_strength_mpa",
  "image": "base64_encoded_image",
  "data_points": 100
}
```

### Get Statistics

```http
GET /api/v1/analysis/statistics?material_type=PLA
```

**Response:**
```json
{
  "statistics": {
    "nozzle_temperature": {
      "count": 100,
      "mean": 220.5,
      "std": 15.2,
      "min": 200.0,
      "max": 250.0,
      "q25": 210.0,
      "q50": 220.0,
      "q75": 230.0
    }
  }
}
```

### Get Correlations

```http
GET /api/v1/analysis/correlations?threshold=0.7&material_type=PLA
```

**Response:**
```json
{
  "correlation_matrix": {...},
  "strong_correlations": [
    {
      "variable1": "nozzle_temperature",
      "variable2": "tensile_strength_mpa",
      "correlation": 0.85,
      "strength": "strong"
    }
  ],
  "significant_pairs": [...]
}
```

### Perform PCA

```http
POST /api/v1/analysis/pca?n_components=2&material_type=PLA
```

**Response:**
```json
{
  "components": [[...], [...]],
  "explained_variance_ratio": [0.65, 0.25],
  "cumulative_variance": [0.65, 0.90],
  "visualization": {...}
}
```

## Usage Examples

### Python Client

```python
from data_analysis_client import DataAnalysisClient

client = DataAnalysisClient()

# Exploratory analysis
result = client.explore_data(material_type="PLA")
print(f"Insights: {result['report']['insights']}")

# Create scatter plot
scatter = client.create_visualization(
    plot_type="scatter",
    x_column="nozzle_temperature",
    y_column="tensile_strength_mpa",
    material_type="PLA"
)
client.save_visualization(scatter, "scatter.png")

# Get statistics
stats = client.get_statistics(material_type="PLA")

# Correlation analysis
corr = client.get_correlations(material_type="PLA", threshold=0.7)

# PCA
pca = client.perform_pca(material_type="PLA", n_components=2)
```

### cURL Examples

```bash
# Exploratory analysis
curl -X POST http://localhost:8000/api/v1/analysis/explore \
  -H "Content-Type: application/json" \
  -d '{"material_type": "PLA", "include_visualizations": true}'

# Create visualization
curl -X POST http://localhost:8000/api/v1/analysis/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "plot_type": "scatter",
    "x_column": "nozzle_temperature",
    "y_column": "tensile_strength_mpa"
  }'

# Get statistics
curl "http://localhost:8000/api/v1/analysis/statistics?material_type=PLA"

# Get correlations
curl "http://localhost:8000/api/v1/analysis/correlations?threshold=0.7"
```

## Visualization Types

### Scatter Plot
- X vs Y relationship
- Optional color coding
- Interactive tooltips

### Correlation Heatmap
- Full correlation matrix
- Color-coded values
- Annotations

### Distribution Plot
- Histogram
- KDE (Kernel Density Estimation)
- Box plot

### Time Series
- Temporal trends
- Multiple series support
- Smooth lines

### Pair Plot
- Scatter matrix
- Distribution diagonals
- Correlation overview

### Cluster Visualization
- Cluster assignments
- Color-coded clusters
- Cluster centers

### PCA Visualization
- Component scatter plot
- Explained variance
- Feature contributions

### Summary Dashboard
- Multiple distributions
- Statistical summaries
- Overview panels

## Analysis Workflow

1. **Data Collection**: Gather experimental data
2. **Exploratory Analysis**: Run comprehensive EDA
3. **Visualization**: Create relevant visualizations
4. **Pattern Discovery**: Identify clusters and trends
5. **Statistical Analysis**: Calculate statistics
6. **Correlation Analysis**: Find relationships
7. **Dimensionality Reduction**: Apply PCA if needed
8. **Insights Generation**: Generate recommendations

## Best Practices

1. **Start with EDA**: Always begin with exploratory analysis
2. **Visualize First**: Create visualizations before statistical tests
3. **Check Assumptions**: Verify normality, linearity, etc.
4. **Multiple Views**: Use different visualization types
5. **Filter Appropriately**: Filter by material type for focused analysis
6. **Interpret Carefully**: Consider context when interpreting results
7. **Document Findings**: Save visualizations and reports

## Performance

- **Small Datasets** (<1000 rows): Fast, all features available
- **Medium Datasets** (1000-10000 rows): Good performance, sampling for pair plots
- **Large Datasets** (>10000 rows): May require sampling or filtering

## Limitations

- Visualizations are static (PNG format)
- Large datasets may require sampling
- Some analyses require minimum data points
- Memory usage scales with dataset size

## Future Enhancements

- [ ] Interactive visualizations (Plotly)
- [ ] Real-time analysis updates
- [ ] Advanced clustering algorithms
- [ ] Time series forecasting
- [ ] Automated insight generation
- [ ] Report generation (PDF)
- [ ] Custom visualization builder
- [ ] Integration with ML models

## Troubleshooting

### No Data Available
- Check experiment filters
- Verify data exists in database
- Check API response for errors

### Visualization Fails
- Ensure required columns exist
- Check data types
- Verify sufficient data points

### PCA Errors
- Need at least 2 numeric columns
- Sufficient data points required
- Check for missing values

## Support

For issues or questions:
- Check API documentation at `/api/v1/docs`
- Review visualization examples
- Check server logs for errors
