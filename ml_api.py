"""
REST endpoints for ML prediction and forecasting.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from am_data_pipeline_postgres import Experiment, get_db
from ml_pipeline import MLPipeline
from restful_api import app


class TrainModelRequest(BaseModel):
    target_col: str = Field(..., description="Target column to predict")
    feature_cols: List[str] = Field(..., description="Feature columns")
    model_type: str = Field("random_forest", description="random_forest or linear")
    material_type: Optional[str] = None


class PredictRequest(BaseModel):
    model_path: str
    records: List[Dict[str, Any]]


class ForecastRequest(BaseModel):
    date_col: str = "build_date"
    value_col: str = "tensile_strength_mpa"
    periods: int = Field(10, ge=1, le=365)
    material_type: Optional[str] = None


def _experiments_to_df(experiments: List[Experiment]) -> pd.DataFrame:
    rows = []
    for exp in experiments:
        row: Dict[str, Any] = {
            "experiment_id": exp.experiment_id,
            "material_type": exp.material_type,
            "build_date": exp.build_date,
            "status": exp.status,
        }
        if exp.process_parameters:
            row.update(
                {
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                    "print_time_hours": exp.process_parameters.print_time_hours,
                }
            )
        if exp.geometry_data:
            row.update(
                {
                    "volume_mm3": exp.geometry_data.volume_mm3,
                    "surface_area_mm2": exp.geometry_data.surface_area_mm2,
                    "complexity_score": exp.geometry_data.complexity_score,
                }
            )
        if exp.quality_metrics:
            row.update(
                {
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "yield_strength_mpa": exp.quality_metrics.yield_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                    "density_g_per_cm3": exp.quality_metrics.density_g_per_cm3,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


@app.post("/api/v1/ml/train", tags=["ML Pipeline"], summary="Train prediction model")
def train_model(payload: TrainModelRequest, db: Session = Depends(get_db)):
    query = db.query(Experiment)
    if payload.material_type:
        query = query.filter(Experiment.material_type == payload.material_type)
    experiments = query.all()
    if not experiments:
        raise HTTPException(status_code=404, detail="No experiments found for training")

    df = _experiments_to_df(experiments)
    pipeline = MLPipeline()
    try:
        result = pipeline.train_regression(
            df=df,
            target_col=payload.target_col,
            feature_cols=payload.feature_cols,
            model_type=payload.model_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "model_name": result.model_name,
        "target": result.target,
        "features": result.features,
        "metrics": result.metrics,
        "model_path": result.model_path,
    }


@app.post("/api/v1/ml/predict", tags=["ML Pipeline"], summary="Predict values")
def predict(payload: PredictRequest):
    pipeline = MLPipeline()
    try:
        predictions = pipeline.predict(payload.model_path, payload.records)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Model file not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return {"predictions": predictions, "count": len(predictions)}


@app.post("/api/v1/ml/forecast", tags=["ML Pipeline"], summary="Forecast a target series")
def forecast(payload: ForecastRequest, db: Session = Depends(get_db)):
    query = db.query(Experiment)
    if payload.material_type:
        query = query.filter(Experiment.material_type == payload.material_type)
    experiments = query.all()
    if not experiments:
        raise HTTPException(status_code=404, detail="No experiments found for forecasting")

    df = _experiments_to_df(experiments)
    pipeline = MLPipeline()
    try:
        result = pipeline.forecast_linear(
            df=df,
            date_col=payload.date_col,
            value_col=payload.value_col,
            periods=payload.periods,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result
