# Data Modeling and ML Pipeline

This module adds prediction and forecasting capabilities for AM experimental data.

## What it provides

- Supervised regression model training (`RandomForestRegressor` or `LinearRegression`)
- Model persistence (`joblib`)
- Batch prediction from saved models
- Lightweight forecasting using linear trend on time-series data
- REST endpoints integrated into the existing `v1` API

## Files

- `ml_pipeline.py` - core training, prediction, forecasting logic
- `ml_api.py` - REST endpoints
- `api_server.py` - unified API entrypoint (registers all modules)

## Endpoints

- `POST /api/v1/ml/train`
  - Train a model using selected target and feature columns
- `POST /api/v1/ml/predict`
  - Predict with a saved model (`model_path`)
- `POST /api/v1/ml/forecast`
  - Forecast future values from historical experiment data

## Train example

```json
{
  "target_col": "tensile_strength_mpa",
  "feature_cols": [
    "nozzle_temperature",
    "print_speed",
    "layer_height",
    "infill_percentage",
    "volume_mm3",
    "material_type"
  ],
  "model_type": "random_forest",
  "material_type": "PLA"
}
```

## Predict example

```json
{
  "model_path": "ml_models/tensile_strength_mpa_random_forest_regressor.joblib",
  "records": [
    {
      "nozzle_temperature": 220,
      "print_speed": 70,
      "layer_height": 0.2,
      "infill_percentage": 30,
      "volume_mm3": 1200,
      "material_type": "PLA"
    }
  ]
}
```

## Forecast example

```json
{
  "date_col": "build_date",
  "value_col": "tensile_strength_mpa",
  "periods": 14,
  "material_type": "PLA"
}
```

## Run

1. Install dependencies:

```bash
pip install -r requirements_postgres.txt
```

2. Start the unified server:

```bash
python api_server.py
```

3. Open docs:

- `http://localhost:8000/api/v1/docs`

## Notes

- The model trainer uses rows where target is present.
- Categorical columns are one-hot encoded, numeric columns are imputed/scaled.
- Forecasting uses a linear trend baseline; for complex seasonality, add ARIMA/Prophet later.
