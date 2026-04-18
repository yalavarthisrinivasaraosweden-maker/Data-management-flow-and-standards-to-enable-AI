"""
AM Experimental Data Management Pipeline - PostgreSQL Version
Robust data storage system with PostgreSQL database
"""

from http import client
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import os
from pathlib import Path
from contextlib import contextmanager

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/am_data_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Experiment(Base):
    __tablename__ = "experiments"
    
    experiment_id = Column(String, primary_key=True, index=True)
    experiment_name = Column(String, nullable=False)
    material_type = Column(String, index=True)
    material_batch = Column(String)
    build_platform = Column(String)
    build_date = Column(DateTime)
    operator = Column(String)
    status = Column(String, default="completed")
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    process_parameters = relationship("ProcessParameter", back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    geometry_data = relationship("GeometryData", back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    quality_metrics = relationship("QualityMetric", back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="experiment", cascade="all, delete-orphan")
    ml_features = relationship("MLFeature", back_populates="experiment", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_exp_material', 'material_type'),
        Index('idx_exp_date', 'build_date'),
    )

class ProcessParameter(Base):
    __tablename__ = "process_parameters"
    
    parameter_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True, nullable=False)
    layer_height = Column(Float)
    print_speed = Column(Float)
    nozzle_temperature = Column(Float)
    bed_temperature = Column(Float)
    infill_percentage = Column(Float)
    infill_pattern = Column(String)
    shell_count = Column(Integer)
    support_enabled = Column(Boolean)
    support_type = Column(String)
    cooling_fan_speed = Column(Float)
    retraction_distance = Column(Float)
    retraction_speed = Column(Float)
    print_time_hours = Column(Float)
    
    experiment = relationship("Experiment", back_populates="process_parameters")
    
    __table_args__ = (
        Index('idx_param_exp', 'experiment_id'),
    )

class GeometryData(Base):
    __tablename__ = "geometry_data"
    
    geometry_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True, nullable=False)
    part_name = Column(String)
    stl_file_path = Column(String)
    volume_mm3 = Column(Float)
    surface_area_mm2 = Column(Float)
    bounding_box_x = Column(Float)
    bounding_box_y = Column(Float)
    bounding_box_z = Column(Float)
    complexity_score = Column(Float)
    support_volume_mm3 = Column(Float)
    
    experiment = relationship("Experiment", back_populates="geometry_data")
    
    __table_args__ = (
        Index('idx_geom_exp', 'experiment_id'),
    )

class QualityMetric(Base):
    __tablename__ = "quality_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True, nullable=False)
    dimensional_accuracy_mm = Column(Float)
    surface_roughness_um = Column(Float)
    tensile_strength_mpa = Column(Float)
    yield_strength_mpa = Column(Float)
    elongation_percent = Column(Float)
    density_g_per_cm3 = Column(Float)
    porosity_percent = Column(Float)
    hardness_hb = Column(Float)
    defect_count = Column(Integer)
    defect_types = Column(Text)
    measurement_date = Column(DateTime)
    measurement_method = Column(String)
    
    experiment = relationship("Experiment", back_populates="quality_metrics")
    
    __table_args__ = (
        Index('idx_quality_exp', 'experiment_id'),
    )

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    sensor_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False)
    sensor_type = Column(String)
    timestamp = Column(DateTime)
    value = Column(Float)
    unit = Column(String)
    location = Column(String)
    
    experiment = relationship("Experiment", back_populates="sensor_data")
    
    __table_args__ = (
        Index('idx_sensor_exp', 'experiment_id'),
        Index('idx_sensor_type', 'sensor_type'),
        Index('idx_sensor_timestamp', 'timestamp'),
    )

class MLFeature(Base):
    __tablename__ = "ml_features"
    
    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String, nullable=False)
    feature_value = Column(Float, nullable=False)
    feature_category = Column(String)
    computed_at = Column(DateTime, server_default=func.now())
    
    experiment = relationship("Experiment", back_populates="ml_features")
    
    __table_args__ = (
        Index('idx_ml_exp', 'experiment_id'),
        Index('idx_ml_name', 'feature_name'),
    )

# Initialize database
def init_db():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
    except SQLAlchemyError as e:
        print(f"✗ Error creating database tables: {e}")
        raise

# Database dependency
def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Initialize on startup
init_db()

app = FastAPI(title="AM Experimental Data Management Pipeline - PostgreSQL")

# Pydantic Models
class ProcessParameters(BaseModel):
    layer_height: Optional[float] = None
    print_speed: Optional[float] = None
    nozzle_temperature: Optional[float] = None
    bed_temperature: Optional[float] = None
    infill_percentage: Optional[float] = None
    infill_pattern: Optional[str] = None
    shell_count: Optional[int] = None
    support_enabled: Optional[bool] = None
    support_type: Optional[str] = None
    cooling_fan_speed: Optional[float] = None
    retraction_distance: Optional[float] = None
    retraction_speed: Optional[float] = None
    print_time_hours: Optional[float] = None

class GeometryDataSchema(BaseModel):
    part_name: Optional[str] = None
    stl_file_path: Optional[str] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    bounding_box_x: Optional[float] = None
    bounding_box_y: Optional[float] = None
    bounding_box_z: Optional[float] = None
    complexity_score: Optional[float] = None
    support_volume_mm3: Optional[float] = None

class QualityMetrics(BaseModel):
    dimensional_accuracy_mm: Optional[float] = None
    surface_roughness_um: Optional[float] = None
    tensile_strength_mpa: Optional[float] = None
    yield_strength_mpa: Optional[float] = None
    elongation_percent: Optional[float] = None
    density_g_per_cm3: Optional[float] = None
    porosity_percent: Optional[float] = None
    hardness_hb: Optional[float] = None
    defect_count: Optional[int] = None
    defect_types: Optional[str] = None
    measurement_date: Optional[datetime] = None
    measurement_method: Optional[str] = None

class ExperimentCreate(BaseModel):
    experiment_id: str
    experiment_name: str
    material_type: Optional[str] = None
    material_batch: Optional[str] = None
    build_platform: Optional[str] = None
    build_date: Optional[datetime] = None
    operator: Optional[str] = None
    status: str = "completed"
    notes: Optional[str] = None
    process_parameters: Optional[ProcessParameters] = None
    geometry_data: Optional[GeometryDataSchema] = None
    quality_metrics: Optional[QualityMetrics] = None

class ExperimentResponse(BaseModel):
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
    process_parameters: Optional[ProcessParameters] = None
    geometry_data: Optional[GeometryDataSchema] = None
    quality_metrics: Optional[QualityMetrics] = None

    class Config:
        from_attributes = True

# Helper Functions
def compute_ml_features(db: Session, experiment_id: str):
    """Compute ML-ready features from experiment data"""
    try:
        # Get experiment data
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        if not exp:
            return []
        
        features = []
        
        # Process parameter features
        if exp.process_parameters:
            pp = exp.process_parameters
            if pp.layer_height:
                features.append(('layer_height', pp.layer_height, 'process'))
            if pp.print_speed:
                features.append(('print_speed', pp.print_speed, 'process'))
            if pp.nozzle_temperature:
                features.append(('nozzle_temp', pp.nozzle_temperature, 'process'))
            if pp.bed_temperature:
                features.append(('bed_temp', pp.bed_temperature, 'process'))
            if pp.infill_percentage:
                features.append(('infill_pct', pp.infill_percentage, 'process'))
            
            # Derived features
            if pp.nozzle_temperature and pp.bed_temperature:
                temp_diff = pp.nozzle_temperature - pp.bed_temperature
                features.append(('temp_difference', temp_diff, 'derived'))
        
        # Geometry features
        if exp.geometry_data:
            gd = exp.geometry_data
            if gd.volume_mm3 and gd.surface_area_mm2 and gd.volume_mm3 > 0:
                sa_vol_ratio = gd.surface_area_mm2 / gd.volume_mm3
                features.append(('surface_area_volume_ratio', sa_vol_ratio, 'geometry'))
            if gd.bounding_box_x and gd.bounding_box_y and gd.bounding_box_z:
                dims = [gd.bounding_box_x, gd.bounding_box_y, gd.bounding_box_z]
                aspect_ratio = max(dims) / min(dims) if min(dims) > 0 else 0
                features.append(('aspect_ratio', aspect_ratio, 'geometry'))
        
        # Quality features
        if exp.quality_metrics:
            qm = exp.quality_metrics
            if qm.tensile_strength_mpa:
                features.append(('tensile_strength', qm.tensile_strength_mpa, 'quality'))
            if qm.surface_roughness_um:
                features.append(('surface_roughness', qm.surface_roughness_um, 'quality'))
            if qm.porosity_percent:
                features.append(('porosity', qm.porosity_percent, 'quality'))
        
        # Delete existing features and insert new ones
        db.query(MLFeature).filter(MLFeature.experiment_id == experiment_id).delete()
        
        for name, value, category in features:
            feature = MLFeature(
                experiment_id=experiment_id,
                feature_name=name,
                feature_value=value,
                feature_category=category
            )
            db.add(feature)
        
        db.commit()
        return features
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error computing ML features: {e}")
        return []

# API Routes
@app.post("/api/experiments", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """Create a new AM experiment record"""
    try:
        # Check if experiment already exists
        existing = db.query(Experiment).filter(Experiment.experiment_id == experiment.experiment_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Experiment ID already exists")
        
        # Create experiment
        db_exp = Experiment(
            experiment_id=experiment.experiment_id,
            experiment_name=experiment.experiment_name,
            material_type=experiment.material_type,
            material_batch=experiment.material_batch,
            build_platform=experiment.build_platform,
            build_date=experiment.build_date,
            operator=experiment.operator,
            status=experiment.status,
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
        
        # Return response
        return ExperimentResponse(
            experiment_id=db_exp.experiment_id, # type: ignore
            experiment_name=db_exp.experiment_name, # type: ignore
            material_type=db_exp.material_type, # type: ignore
            material_batch=db_exp.material_batch, # type: ignore
            build_platform=db_exp.build_platform, # type: ignore
            build_date=db_exp.build_date, # type: ignore
            operator=db_exp.operator, # type: ignore
            status=db_exp.status, # type: ignore
            notes=db_exp.notes, # type: ignore
            created_at=db_exp.created_at, # type: ignore
            updated_at=db_exp.updated_at, # type: ignore
            process_parameters=ProcessParameters(**db_exp.process_parameters.__dict__) if db_exp.process_parameters else None,
            geometry_data=GeometryData(**db_exp.geometry_data.__dict__) if db_exp.geometry_data else None,
            quality_metrics=QualityMetrics(**db_exp.quality_metrics.__dict__) if db_exp.quality_metrics else None
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments", response_model=List[ExperimentResponse])
def list_experiments(
    material_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List experiments with optional filtering"""
    try:
        query = db.query(Experiment)
        
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        if status:
            query = query.filter(Experiment.status == status)
        
        experiments = query.order_by(Experiment.build_date.desc()).offset(offset).limit(limit).all()
        
        result = []
        for exp in experiments:
            result.append(ExperimentResponse(
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
                process_parameters=ProcessParameters(**exp.process_parameters.__dict__) if exp.process_parameters else None,
                geometry_data=GeometryData(**exp.geometry_data.__dict__) if exp.geometry_data else None,
                quality_metrics=QualityMetrics(**exp.quality_metrics.__dict__) if exp.quality_metrics else None
            ))
        
        return result
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Get a specific experiment by ID"""
    try:
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return ExperimentResponse(
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
            process_parameters=ProcessParameters(**exp.process_parameters.__dict__) if exp.process_parameters else None,
            geometry_data=GeometryData(**exp.geometry_data.__dict__) if exp.geometry_data else None,
            quality_metrics=QualityMetrics(**exp.quality_metrics.__dict__) if exp.quality_metrics else None
        )
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}/ml-features")
def get_ml_features(experiment_id: str, db: Session = Depends(get_db)):
    """Get ML-ready features for an experiment"""
    try:
        features = db.query(MLFeature).filter(MLFeature.experiment_id == experiment_id).all()
        
        if not features:
            # Compute features if they don't exist
            compute_ml_features(db, experiment_id)
            features = db.query(MLFeature).filter(MLFeature.experiment_id == experiment_id).all()
        
        return {
            "experiment_id": experiment_id,
            "features": {f.feature_name: f.feature_value for f in features},
            "categories": {f.feature_name: f.feature_category for f in features}
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/export/ml-dataset")
def export_ml_dataset(
    format: str = Query("csv", regex="^(csv|parquet|json)$"),
    material_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export dataset in ML-ready format"""
    try:
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
        
        # Export based on format
        if format == "csv":
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=am_ml_dataset.csv"}
            )
        elif format == "parquet":
            output = BytesIO()
            df.to_parquet(output, index=False)
            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/octet-stream",
                headers={"Content-Disposition": "attachment; filename=am_ml_dataset.parquet"}
            )
        else:  # json
            return df.to_dict(orient="records")
            
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary of the dataset"""
    try:
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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/experiments/{experiment_id}/sensor-data")
def add_sensor_data(
    experiment_id: str,
    sensor_type: str,
    timestamp: datetime,
    value: float,
    unit: str,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Add sensor data point"""
    try:
        # Verify experiment exists
        exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        sensor_data = SensorData(
            experiment_id=experiment_id,
            sensor_type=sensor_type,
            timestamp=timestamp,
            value=value,
            unit=unit,
            location=location
        )
        db.add(sensor_data)
        db.commit()
        
        return {"message": "Sensor data added successfully"}
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}/sensor-data")
def get_sensor_data(
    experiment_id: str,
    sensor_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get sensor data for an experiment"""
    try:
        query = db.query(SensorData).filter(SensorData.experiment_id == experiment_id)
        
        if sensor_type:
            query = query.filter(SensorData.sensor_type == sensor_type)
        
        sensor_data = query.order_by(SensorData.timestamp).all()
        
        return [{
            "sensor_id": sd.sensor_id,
            "experiment_id": sd.experiment_id,
            "sensor_type": sd.sensor_type,
            "timestamp": sd.timestamp.isoformat() if sd.timestamp else None, # type: ignore
            "value": sd.value,
            "unit": sd.unit,
            "location": sd.location
        } for sd in sensor_data]
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        client.admin.command('ping') # type: ignore
        db.execute("SELECT 1") # type: ignore
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Serve frontend
@app.get("/")
def read_root():
    # Serve advanced dashboard if available, otherwise fallback to basic
    if os.path.exists("am_dashboard_advanced.html"):
        return FileResponse("am_dashboard_advanced.html")
    return FileResponse("am_dashboard.html")

@app.get("/dashboard/basic")
def read_basic_dashboard():
    return FileResponse("am_dashboard.html")

@app.get("/dashboard/advanced")
def read_advanced_dashboard():
    return FileResponse("am_dashboard_advanced.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
