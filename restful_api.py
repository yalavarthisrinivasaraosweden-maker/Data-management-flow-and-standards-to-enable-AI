"""
RESTful API for AM Experimental Data Management
Comprehensive REST API with proper conventions, versioning, and documentation
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import os

# Import database models and dependencies
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from am_data_pipeline_postgres import (
    get_db, Experiment, ProcessParameter, GeometryData,
    GeometryDataSchema, QualityMetric, SensorData, MLFeature,
    compute_ml_features
)

# API Version
API_VERSION = "v1"

# Initialize FastAPI app
app = FastAPI(
    title="AM Experimental Data Management API",
    description="RESTful API for managing and accessing AM experimental data",
    version="1.0.0",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
    openapi_url=f"/api/{API_VERSION}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AM Experimental Data Management API",
        version="1.0.0",
        description="""
        ## RESTful API for AM Experimental Data Management
        
        This API provides comprehensive endpoints for:
        - Creating, reading, updating, and deleting experiments
        - Managing process parameters, geometry data, and quality metrics
        - Accessing ML-ready features and datasets
        - Querying and filtering experimental data
        - Exporting data in various formats
        
        ## Authentication
        Currently, the API is open. For production, implement authentication.
        
        ## Rate Limiting
        Default rate limit: 100 requests per minute per IP.
        
        ## Versioning
        Current API version: v1
        All endpoints are prefixed with `/api/v1`
        """,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Enums
class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class ExportFormat(str, Enum):
    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"

# Pydantic Models
class ProcessParametersModel(BaseModel):
    layer_height: Optional[float] = Field(None, ge=0, description="Layer height in mm")
    print_speed: Optional[float] = Field(None, ge=0, description="Print speed in mm/s")
    nozzle_temperature: Optional[float] = Field(None, ge=0, description="Nozzle temperature in °C")
    bed_temperature: Optional[float] = Field(None, ge=0, description="Bed temperature in °C")
    infill_percentage: Optional[float] = Field(None, ge=0, le=100, description="Infill percentage")
    infill_pattern: Optional[str] = Field(None, description="Infill pattern type")
    shell_count: Optional[int] = Field(None, ge=0, description="Number of shell layers")
    support_enabled: Optional[bool] = Field(None, description="Whether supports are enabled")
    support_type: Optional[str] = Field(None, description="Type of support structure")
    cooling_fan_speed: Optional[float] = Field(None, ge=0, le=100, description="Cooling fan speed %")
    retraction_distance: Optional[float] = Field(None, ge=0, description="Retraction distance in mm")
    retraction_speed: Optional[float] = Field(None, ge=0, description="Retraction speed in mm/s")
    print_time_hours: Optional[float] = Field(None, ge=0, description="Total print time in hours")

class GeometryDataModel(BaseModel):
    part_name: Optional[str] = None
    stl_file_path: Optional[str] = None
    volume_mm3: Optional[float] = Field(None, ge=0)
    surface_area_mm2: Optional[float] = Field(None, ge=0)
    bounding_box_x: Optional[float] = Field(None, ge=0)
    bounding_box_y: Optional[float] = Field(None, ge=0)
    bounding_box_z: Optional[float] = Field(None, ge=0)
    complexity_score: Optional[float] = None
    support_volume_mm3: Optional[float] = Field(None, ge=0)

class QualityMetricsModel(BaseModel):
    dimensional_accuracy_mm: Optional[float] = None
    surface_roughness_um: Optional[float] = Field(None, ge=0)
    tensile_strength_mpa: Optional[float] = Field(None, ge=0)
    yield_strength_mpa: Optional[float] = Field(None, ge=0)
    elongation_percent: Optional[float] = Field(None, ge=0)
    density_g_per_cm3: Optional[float] = Field(None, ge=0)
    porosity_percent: Optional[float] = Field(None, ge=0, le=100)
    hardness_hb: Optional[float] = Field(None, ge=0)
    defect_count: Optional[int] = Field(None, ge=0)
    defect_types: Optional[str] = None
    measurement_date: Optional[datetime] = None
    measurement_method: Optional[str] = None

class ExperimentCreateModel(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=100, description="Unique experiment identifier")
    experiment_name: str = Field(..., min_length=1, max_length=200, description="Experiment name")
    material_type: Optional[str] = Field(None, max_length=50)
    material_batch: Optional[str] = Field(None, max_length=50)
    build_platform: Optional[str] = Field(None, max_length=100)
    build_date: Optional[datetime] = None
    operator: Optional[str] = Field(None, max_length=100)
    status: ExperimentStatus = ExperimentStatus.COMPLETED
    notes: Optional[str] = None
    process_parameters: Optional[ProcessParametersModel] = None
    geometry_data: Optional[GeometryDataModel] = None
    quality_metrics: Optional[QualityMetricsModel] = None

class ExperimentUpdateModel(BaseModel):
    experiment_name: Optional[str] = Field(None, min_length=1, max_length=200)
    material_type: Optional[str] = Field(None, max_length=50)
    material_batch: Optional[str] = Field(None, max_length=50)
    build_platform: Optional[str] = Field(None, max_length=100)
    build_date: Optional[datetime] = None
    operator: Optional[str] = Field(None, max_length=100)
    status: Optional[ExperimentStatus] = None
    notes: Optional[str] = None
    process_parameters: Optional[ProcessParametersModel] = None
    geometry_data: Optional[GeometryDataModel] = None
    quality_metrics: Optional[QualityMetricsModel] = None

class ExperimentResponseModel(BaseModel):
    experiment_id: str
    experiment_name: str
    material_type: Optional[str]
    material_batch: Optional[str]
    build_platform: Optional[str]
    build_date: Optional[datetime]
    operator: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    process_parameters: Optional[ProcessParametersModel] = None
    geometry_data: Optional[GeometryDataModel] = None
    quality_metrics: Optional[QualityMetricsModel] = None

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[ExperimentResponseModel]
    total: int
    page: int
    page_size: int
    pages: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None

# Helper Functions
def convert_experiment_to_response(exp: Experiment) -> ExperimentResponseModel:
    """Convert database experiment to response model"""
    return ExperimentResponseModel(
        experiment_id=exp.experiment_id, # type: ignore
        experiment_name=exp.experiment_name, # type: ignore
        material_type=exp.material_type, # type: ignore
        material_batch=exp.material_batch, # type: ignore
        build_platform=exp.build_platform, # type: ignore
        build_date=exp.build_date, # type: ignore
        operator=exp.operator, # type: ignore
        status=exp.status, # type: ignore
        notes=exp.notes, # type: ignore
        created_at=exp.created_at, # type: ignore
        updated_at=exp.updated_at, # type: ignore
        process_parameters=ProcessParametersModel(**exp.process_parameters.__dict__) if exp.process_parameters else None,
        geometry_data=GeometryDataModel(**exp.geometry_data.__dict__) if exp.geometry_data else None,
        quality_metrics=QualityMetricsModel(**exp.quality_metrics.__dict__) if exp.quality_metrics else None
    )

# API Routes

# REPLACE with:
@app.get("/", tags=["Root"])
def root():
    """Serve the main dashboard"""
    from fastapi.responses import FileResponse
    import os
    if os.path.exists("am_dashboard.html"):
        return FileResponse("am_dashboard.html")
    # Fallback to JSON if HTML file not found
    return {
        "name": "AM Experimental Data Management API",
        "version": "1.0.0",
        "api_version": API_VERSION,
        "docs": f"/api/{API_VERSION}/docs",
        "status": "operational"
    }

@app.get(f"/api/{API_VERSION}/info", tags=["Root"])
def api_info():
    """API information endpoint"""
    return {
        "name": "AM Experimental Data Management API",
        "version": "1.0.0",
        "api_version": API_VERSION,
        "docs": f"/api/{API_VERSION}/docs",
        "dashboard": "/",
        "advanced_dashboard": "/dashboard/advanced",
        "status": "operational"
    }

# FIND and replace the entire health_check function:
@app.get(f"/api/{API_VERSION}/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Experiment Endpoints

@app.post(
    f"/api/{API_VERSION}/experiments",
    response_model=ExperimentResponseModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Experiments"],
    summary="Create a new experiment",
    description="Create a new AM experiment with optional process parameters, geometry data, and quality metrics"
)
def create_experiment(
    experiment: ExperimentCreateModel,
    db: Session = Depends(get_db)
):
    """Create a new experiment"""
    try:
        # Check if experiment already exists
        existing = db.query(Experiment).filter(Experiment.experiment_id == experiment.experiment_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Experiment with ID '{experiment.experiment_id}' already exists"
            )
        
        # Create experiment
        db_exp = Experiment(
            experiment_id=experiment.experiment_id,
            experiment_name=experiment.experiment_name,
            material_type=experiment.material_type,
            material_batch=experiment.material_batch,
            build_platform=experiment.build_platform,
            build_date=experiment.build_date,
            operator=experiment.operator,
            status=experiment.status.value,
            notes=experiment.notes
        )
        db.add(db_exp)
        
        # Add process parameters
        if experiment.process_parameters:
            pp = ProcessParameter(
                experiment_id=experiment.experiment_id,
                **experiment.process_parameters.dict(exclude_none=True)
            )
            db.add(pp)
        
        # Add geometry data
        if experiment.geometry_data:
            gd = GeometryData(
                experiment_id=experiment.experiment_id,
                **experiment.geometry_data.dict(exclude_none=True)
            )
            db.add(gd)
        
        # Add quality metrics
        if experiment.quality_metrics:
            qm = QualityMetric(
                experiment_id=experiment.experiment_id,
                **experiment.quality_metrics.dict(exclude_none=True)
            )
            db.add(qm)
        
        db.commit()
        db.refresh(db_exp)
        
        # Compute ML features
        compute_ml_features(db, experiment.experiment_id)
        
        return convert_experiment_to_response(db_exp)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    f"/api/{API_VERSION}/experiments",
    response_model=PaginatedResponse,
    tags=["Experiments"],
    summary="List experiments",
    description="Get a paginated list of experiments with optional filtering and sorting"
)
def list_experiments(
    material_type: Optional[str] = Query(None, description="Filter by material type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    build_platform: Optional[str] = Query(None, description="Filter by build platform"),
    date_from: Optional[datetime] = Query(None, description="Filter experiments from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter experiments to this date"),
    sort_by: Optional[str] = Query("build_date", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List experiments with pagination and filtering"""
    try:
        query = db.query(Experiment)
        
        # Apply filters
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        if status:
            query = query.filter(Experiment.status == status)
        if operator:
            query = query.filter(Experiment.operator == operator)
        if build_platform:
            query = query.filter(Experiment.build_platform == build_platform)
        if date_from:
            query = query.filter(Experiment.build_date >= date_from)
        if date_to:
            query = query.filter(Experiment.build_date <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_field = getattr(Experiment, sort_by, Experiment.build_date) # type: ignore
        if sort_order == SortOrder.DESC:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        experiments = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=[convert_experiment_to_response(exp) for exp in experiments],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # type: ignore
            detail=f"Database error: {str(e)}"
        )

@app.get(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}",
    response_model=ExperimentResponseModel,
    tags=["Experiments"],
    summary="Get experiment by ID",
    description="Retrieve a specific experiment by its unique identifier"
)
def get_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Get a specific experiment by ID"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        return convert_experiment_to_response(exp)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.put(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}",
    response_model=ExperimentResponseModel,
    tags=["Experiments"],
    summary="Update experiment",
    description="Update an existing experiment. Only provided fields will be updated."
)
def update_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    experiment_update: ExperimentUpdateModel = ..., # type: ignore
    db: Session = Depends(get_db)
):
    """Update an existing experiment"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        # Update experiment fields
        update_data = experiment_update.dict(exclude_none=True, exclude={'process_parameters', 'geometry_data', 'quality_metrics'})
        for field, value in update_data.items():
            if field == 'status' and isinstance(value, ExperimentStatus):
                setattr(exp, field, value.value)
            else:
                setattr(exp, field, value)
        
        # Update process parameters
        if experiment_update.process_parameters:
            if exp.process_parameters:
                for field, value in experiment_update.process_parameters.dict(exclude_none=True).items():
                    setattr(exp.process_parameters, field, value)
            else:
                pp = ProcessParameter(
                    experiment_id=experiment_id,
                    **experiment_update.process_parameters.dict(exclude_none=True)
                )
                db.add(pp)
        
        # Update geometry data
        if experiment_update.geometry_data:
            if exp.geometry_data:
                for field, value in experiment_update.geometry_data.dict(exclude_none=True).items():
                    setattr(exp.geometry_data, field, value)
            else:
                gd = GeometryData(
                    experiment_id=experiment_id,
                    **experiment_update.geometry_data.dict(exclude_none=True)
                )
                db.add(gd)
        
        # Update quality metrics
        if experiment_update.quality_metrics:
            if exp.quality_metrics:
                for field, value in experiment_update.quality_metrics.dict(exclude_none=True).items():
                    setattr(exp.quality_metrics, field, value)
            else:
                qm = QualityMetric(
                    experiment_id=experiment_id,
                    **experiment_update.quality_metrics.dict(exclude_none=True)
                )
                db.add(qm)
        
        exp.updated_at = datetime.now() # type: ignore
        db.commit()
        db.refresh(exp)
        
        # Recompute ML features
        compute_ml_features(db, experiment_id)
        
        return convert_experiment_to_response(exp)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.delete(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Experiments"],
    summary="Delete experiment",
    description="Delete an experiment and all associated data"
)
def delete_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Delete an experiment"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        db.delete(exp)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Process Parameters Endpoints

@app.get(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}/process-parameters",
    response_model=ProcessParametersModel,
    tags=["Process Parameters"],
    summary="Get process parameters",
    description="Get process parameters for a specific experiment"
)
def get_process_parameters(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Get process parameters for an experiment"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        if not exp.process_parameters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process parameters not found for experiment '{experiment_id}'"
            )
        
        return ProcessParametersModel(**exp.process_parameters.__dict__)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Quality Metrics Endpoints

@app.get(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}/quality-metrics",
    response_model=QualityMetricsModel,
    tags=["Quality Metrics"],
    summary="Get quality metrics",
    description="Get quality metrics for a specific experiment"
)
def get_quality_metrics(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Get quality metrics for an experiment"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        if not exp.quality_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quality metrics not found for experiment '{experiment_id}'"
            )
        
        return QualityMetricsModel(**exp.quality_metrics.__dict__)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# ML Features Endpoints

@app.get(
    f"/api/{API_VERSION}/experiments/{{experiment_id}}/ml-features",
    tags=["ML Features"],
    summary="Get ML features",
    description="Get ML-ready features for a specific experiment"
)
def get_ml_features(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Get ML-ready features for an experiment"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found"
            )
        
        features = db.query(MLFeature).filter(MLFeature.experiment_id == experiment_id).all()
        
        if not features:
            # Compute features if they don't exist
            compute_ml_features(db, experiment_id)
            features = db.query(MLFeature).filter(MLFeature.experiment_id == experiment_id).all()
        
        return {
            "experiment_id": experiment_id,
            "features": {f.feature_name: f.feature_value for f in features},
            "categories": {f.feature_name: f.feature_category for f in features},
            "count": len(features)
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Analytics Endpoints

@app.get(
    f"/api/{API_VERSION}/analytics/summary",
    tags=["Analytics"],
    summary="Get analytics summary",
    description="Get overall statistics and analytics summary of the dataset"
)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary"""
    try:
        from sqlalchemy import func
        
        # Total experiments
        total_experiments = db.query(Experiment).count()
        
        # Material distribution
        material_dist = db.query(
            Experiment.material_type,
            func.count(Experiment.experiment_id)
        ).group_by(Experiment.material_type).all()
        material_dist_dict = {mat: count for mat, count in material_dist if mat}
        
        # Average quality metrics
        avg_quality = db.query(
            func.avg(QualityMetric.tensile_strength_mpa),
            func.avg(QualityMetric.surface_roughness_um),
            func.avg(QualityMetric.porosity_percent)
        ).first()
        
        # Process parameter ranges
        param_ranges = db.query(
            func.min(ProcessParameter.nozzle_temperature),
            func.max(ProcessParameter.nozzle_temperature),
            func.avg(ProcessParameter.nozzle_temperature),
            func.min(ProcessParameter.print_speed),
            func.max(ProcessParameter.print_speed),
            func.avg(ProcessParameter.print_speed)
        ).first()
        
        return {
            "total_experiments": total_experiments,
            "material_distribution": material_dist_dict,
            "average_quality_metrics": {
                "tensile_strength_mpa": float(avg_quality[0]) if avg_quality[0] else None, # type: ignore
                "surface_roughness_um": float(avg_quality[1]) if avg_quality[1] else None, # type: ignore
                "porosity_percent": float(avg_quality[2]) if avg_quality[2] else None # type: ignore
            },
            "process_parameter_ranges": {
                "nozzle_temperature": {
                    "min": float(param_ranges[0]) if param_ranges[0] else None, # type: ignore
                    "max": float(param_ranges[1]) if param_ranges[1] else None, # type: ignore
                    "avg": float(param_ranges[2]) if param_ranges[2] else None # type: ignore
                },
                "print_speed": {
                    "min": float(param_ranges[3]) if param_ranges[3] else None, # type: ignore
                    "max": float(param_ranges[4]) if param_ranges[4] else None, # type: ignore
                    "avg": float(param_ranges[5]) if param_ranges[5] else None # type: ignore
                }
            }
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Export Endpoints

@app.get(
    f"/api/{API_VERSION}/export/dataset",
    tags=["Export"],
    summary="Export dataset",
    description="Export experimental data in various formats for ML/AI applications"
)
def export_dataset(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    material_type: Optional[str] = Query(None, description="Filter by material type"),
    db: Session = Depends(get_db)
):
    """Export dataset"""
    try:
        import pandas as pd
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        
        query = db.query(
            Experiment.experiment_id,
            Experiment.material_type,
            Experiment.material_batch,
            Experiment.build_date,
            ProcessParameter.layer_height,
            ProcessParameter.print_speed,
            ProcessParameter.nozzle_temperature,
            ProcessParameter.bed_temperature,
            ProcessParameter.infill_percentage,
            ProcessParameter.infill_pattern,
            ProcessParameter.shell_count,
            ProcessParameter.support_enabled,
            ProcessParameter.print_time_hours,
            GeometryData.volume_mm3,
            GeometryData.surface_area_mm2,
            GeometryData.complexity_score,
            QualityMetric.tensile_strength_mpa,
            QualityMetric.yield_strength_mpa,
            QualityMetric.surface_roughness_um,
            QualityMetric.porosity_percent,
            QualityMetric.density_g_per_cm3,
            QualityMetric.defect_count
        ).outerjoin(ProcessParameter).outerjoin(GeometryData).outerjoin(QualityMetric)
        
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        df = pd.read_sql(query.statement, db.bind) # type: ignore
        
        if format == ExportFormat.CSV:
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=am_dataset.csv"}
            )
        elif format == ExportFormat.PARQUET:
            output = BytesIO()
            df.to_parquet(output, index=False)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/octet-stream",
                headers={"Content-Disposition": "attachment; filename=am_dataset.parquet"}
            )
        else:  # JSON
            return df.to_dict(orient="records")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export error: {str(e)}"
        )

# Error Handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500,
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
