"""
Data Quality API Endpoints
RESTful API for data validation, cleaning, and preprocessing
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

# Import data quality pipeline
from data_quality_pipeline import (
    DataQualityPipeline, ValidationLevel, DataQualityReport,
    DataQualityIssue
)

# Import database
from am_data_pipeline_postgres import get_db, Experiment

# Import existing API
from restful_api import app

# Pydantic Models
class ValidationRequestModel(BaseModel):
    experiment_id: Optional[str] = None
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    experiments: Optional[List[Dict[str, Any]]] = None

class CleaningRequestModel(BaseModel):
    remove_outliers: bool = True
    handle_missing: bool = True
    remove_duplicates: bool = True
    normalize: bool = False
    outlier_method: str = "iqr"  # "iqr" or "zscore"
    missing_strategy: str = "mean"  # "mean", "median", "mode", "knn"

class PreprocessingRequestModel(BaseModel):
    normalize: bool = True
    normalize_method: str = "standard"  # "standard", "minmax", "robust"
    feature_engineering: bool = True
    remove_correlated: bool = False
    correlation_threshold: float = 0.95

# API Endpoints

@app.post(
    "/api/v1/data-quality/validate",
    response_model=DataQualityReport,
    tags=["Data Quality"],
    summary="Validate experiments",
    description="Validate experiment data and generate quality report"
)
def validate_experiments(
    request: ValidationRequestModel = ..., # type: ignore
    db: Session = Depends(get_db)
):
    """Validate experiments"""
    try:
        pipeline = DataQualityPipeline(validation_level=request.validation_level)
        
        if request.experiments:
            # Validate provided experiments
            experiments = request.experiments
        elif request.experiment_id:
            # Get experiment from database
            exp = db.query(Experiment).filter(Experiment.experiment_id == request.experiment_id).first()
            if not exp:
                raise HTTPException(status_code=404, detail="Experiment not found")
            
            # Convert to dict
            experiments = [{
                "experiment_id": exp.experiment_id,
                "process_parameters": {
                    "layer_height": exp.process_parameters.layer_height if exp.process_parameters else None,
                    "print_speed": exp.process_parameters.print_speed if exp.process_parameters else None,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature if exp.process_parameters else None,
                    "bed_temperature": exp.process_parameters.bed_temperature if exp.process_parameters else None,
                    "infill_percentage": exp.process_parameters.infill_percentage if exp.process_parameters else None,
                } if exp.process_parameters else {},
                "quality_metrics": {
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa if exp.quality_metrics else None,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um if exp.quality_metrics else None,
                    "porosity_percent": exp.quality_metrics.porosity_percent if exp.quality_metrics else None,
                } if exp.quality_metrics else {},
                "geometry_data": {
                    "volume_mm3": exp.geometry_data.volume_mm3 if exp.geometry_data else None,
                    "surface_area_mm2": exp.geometry_data.surface_area_mm2 if exp.geometry_data else None,
                } if exp.geometry_data else {},
            }]
        else:
            # Get all experiments
            all_experiments = db.query(Experiment).all()
            experiments = []
            for exp in all_experiments:
                experiments.append({
                    "experiment_id": exp.experiment_id,
                    "process_parameters": exp.process_parameters.__dict__ if exp.process_parameters else {},
                    "quality_metrics": exp.quality_metrics.__dict__ if exp.quality_metrics else {},
                    "geometry_data": exp.geometry_data.__dict__ if exp.geometry_data else {},
                })
        
        report = pipeline.generate_quality_report(experiments, request.experiment_id)
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )

@app.post(
    "/api/v1/data-quality/clean",
    tags=["Data Quality"],
    summary="Clean dataset",
    description="Clean dataset by removing outliers, handling missing values, etc."
)
def clean_dataset(
    experiment_ids: Optional[List[str]] = Body(None, description="List of experiment IDs"),
    material_type: Optional[str] = Query(None, description="Filter by material type"),
    cleaning_options: CleaningRequestModel = Body(CleaningRequestModel()),
    db: Session = Depends(get_db)
):
    """Clean dataset"""
    try:
        # Get experiments
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {"experiment_id": exp.experiment_id}
            
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Clean data
        pipeline = DataQualityPipeline()
        df_cleaned, cleaning_log = pipeline.clean_dataset(
            df,
            remove_outliers=cleaning_options.remove_outliers,
            handle_missing=cleaning_options.handle_missing,
            remove_duplicates=cleaning_options.remove_duplicates,
            normalize=cleaning_options.normalize
        )
        
        return {
            "cleaned_data": df_cleaned.to_dict(orient="records"),
            "cleaning_log": cleaning_log,
            "statistics": {
                "initial_rows": len(df),
                "final_rows": len(df_cleaned),
                "removed_rows": len(df) - len(df_cleaned)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleaning error: {str(e)}"
        )

@app.post(
    "/api/v1/data-quality/preprocess",
    tags=["Data Quality"],
    summary="Preprocess dataset",
    description="Preprocess dataset for ML/AI applications"
)
def preprocess_dataset(
    experiment_ids: Optional[List[str]] = Body(None),
    material_type: Optional[str] = Query(None),
    preprocessing_options: PreprocessingRequestModel = Body(PreprocessingRequestModel()),
    db: Session = Depends(get_db)
):
    """Preprocess dataset"""
    try:
        # Get experiments (similar to clean endpoint)
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {"experiment_id": exp.experiment_id}
            
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Preprocess
        pipeline = DataQualityPipeline()
        
        # Handle missing values first
        df = pipeline.handle_missing_values(df, strategy="mean")
        
        # Normalize
        if preprocessing_options.normalize:
            import numpy as np
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col != "experiment_id"]
            df = pipeline.normalize_data(df, numeric_cols, method=preprocessing_options.normalize_method)
        
        # Feature engineering
        if preprocessing_options.feature_engineering:
            # Add derived features
            if "nozzle_temperature" in df.columns and "bed_temperature" in df.columns:
                df["temp_difference"] = df["nozzle_temperature"] - df["bed_temperature"]
            
            if "volume_mm3" in df.columns and "surface_area_mm2" in df.columns:
                df["sa_vol_ratio"] = df["surface_area_mm2"] / (df["volume_mm3"] + 1e-10)
        
        # Remove highly correlated features
        if preprocessing_options.remove_correlated:
            import numpy as np
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            corr_matrix = df[numeric_cols].corr().abs()
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > preprocessing_options.correlation_threshold)]
            df = df.drop(columns=to_drop)
        
        return {
            "preprocessed_data": df.to_dict(orient="records"),
            "preprocessing_info": {
                "normalized": preprocessing_options.normalize,
                "feature_engineering": preprocessing_options.feature_engineering,
                "removed_correlated": preprocessing_options.remove_correlated,
                "final_features": df.columns.tolist()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preprocessing error: {str(e)}"
        )

@app.get(
    "/api/v1/data-quality/issues",
    tags=["Data Quality"],
    summary="Get data quality issues",
    description="Get all data quality issues for experiments"
)
def get_quality_issues(
    experiment_id: Optional[str] = Query(None),
    material_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="Filter by severity: error, warning, info"),
    db: Session = Depends(get_db)
):
    """Get data quality issues"""
    try:
        pipeline = DataQualityPipeline()
        
        # Get experiments
        query = db.query(Experiment)
        if experiment_id:
            query = query.filter(Experiment.experiment_id == experiment_id)
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        all_issues = []
        for exp in experiments:
            exp_dict = {
                "experiment_id": exp.experiment_id,
                "process_parameters": exp.process_parameters.__dict__ if exp.process_parameters else {},
                "quality_metrics": exp.quality_metrics.__dict__ if exp.quality_metrics else {},
                "geometry_data": exp.geometry_data.__dict__ if exp.geometry_data else {},
            }
            issues = pipeline.validate_experiment(exp_dict)
            all_issues.extend(issues)
        
        # Filter by severity
        if severity:
            all_issues = [issue for issue in all_issues if issue.severity == severity]
        
        return {
            "total_issues": len(all_issues),
            "issues": [issue.dict() for issue in all_issues]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
