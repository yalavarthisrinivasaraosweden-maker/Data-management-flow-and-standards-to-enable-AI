"""
AM Experimental Data Management Pipeline
Supports efficient storage, easy access, and ML/AI applications
"""

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
import json
import pandas as pd
import numpy as np
from io import BytesIO
import os
from pathlib import Path

app = FastAPI(title="AM Experimental Data Management Pipeline")

# Allow local HTML opened as file:// to call this API (and normal browser dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "am_data.db"
DATA_DIR = Path("am_data_storage")
DATA_DIR.mkdir(exist_ok=True)

def init_db():
    """Initialize the database with AM-specific tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Experiments table - main experiment records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            experiment_id TEXT PRIMARY KEY,
            experiment_name TEXT NOT NULL,
            material_type TEXT,
            material_batch TEXT,
            build_platform TEXT,
            build_date TIMESTAMP,
            operator TEXT,
            status TEXT DEFAULT 'completed',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Process parameters - AM process settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS process_parameters (
            parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            layer_height REAL,
            print_speed REAL,
            nozzle_temperature REAL,
            bed_temperature REAL,
            infill_percentage REAL,
            infill_pattern TEXT,
            shell_count INTEGER,
            support_enabled BOOLEAN,
            support_type TEXT,
            cooling_fan_speed REAL,
            retraction_distance REAL,
            retraction_speed REAL,
            print_time_hours REAL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # Geometry data - build geometry information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geometry_data (
            geometry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            part_name TEXT,
            stl_file_path TEXT,
            volume_mm3 REAL,
            surface_area_mm2 REAL,
            bounding_box_x REAL,
            bounding_box_y REAL,
            bounding_box_z REAL,
            complexity_score REAL,
            support_volume_mm3 REAL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # Quality metrics - measured quality characteristics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            dimensional_accuracy_mm REAL,
            surface_roughness_um REAL,
            tensile_strength_mpa REAL,
            yield_strength_mpa REAL,
            elongation_percent REAL,
            density_g_per_cm3 REAL,
            porosity_percent REAL,
            hardness_hb REAL,
            defect_count INTEGER,
            defect_types TEXT,
            measurement_date TIMESTAMP,
            measurement_method TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # Sensor data - time-series sensor readings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            sensor_type TEXT,
            timestamp TIMESTAMP,
            value REAL,
            unit TEXT,
            location TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # ML features - precomputed features for ML/AI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_features (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            feature_name TEXT,
            feature_value REAL,
            feature_category TEXT,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # Data versions - track data changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            version_number INTEGER,
            change_description TEXT,
            changed_fields TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    """)
    
    # Create indexes for efficient querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_material ON experiments(material_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_date ON experiments(build_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_param_exp ON process_parameters(experiment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_exp ON quality_metrics(experiment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_exp ON sensor_data(experiment_id)")
    
    conn.commit()
    conn.close()

init_db()

# Pydantic Models
class ProcessParameters(BaseModel):
    layer_height: Optional[float] = Field(None, description="Layer height in mm")
    print_speed: Optional[float] = Field(None, description="Print speed in mm/s")
    nozzle_temperature: Optional[float] = Field(None, description="Nozzle temperature in °C")
    bed_temperature: Optional[float] = Field(None, description="Bed temperature in °C")
    infill_percentage: Optional[float] = Field(None, description="Infill percentage")
    infill_pattern: Optional[str] = Field(None, description="Infill pattern type")
    shell_count: Optional[int] = Field(None, description="Number of shell layers")
    support_enabled: Optional[bool] = Field(None, description="Whether supports are enabled")
    support_type: Optional[str] = Field(None, description="Type of support structure")
    cooling_fan_speed: Optional[float] = Field(None, description="Cooling fan speed %")
    retraction_distance: Optional[float] = Field(None, description="Retraction distance in mm")
    retraction_speed: Optional[float] = Field(None, description="Retraction speed in mm/s")
    print_time_hours: Optional[float] = Field(None, description="Total print time in hours")

class GeometryData(BaseModel):
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
    geometry_data: Optional[GeometryData] = None
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
    geometry_data: Optional[GeometryData] = None
    quality_metrics: Optional[QualityMetrics] = None

# Helper Functions
def get_db_connection():
    return sqlite3.connect(DB_FILE)

def compute_ml_features(experiment_id: str):
    """Compute ML-ready features from experiment data"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    
    # Get all data for this experiment
    cursor = conn.cursor()
    
    # Get process parameters
    cursor.execute("SELECT * FROM process_parameters WHERE experiment_id = ?", (experiment_id,))
    params = cursor.fetchone()
    
    # Get quality metrics
    cursor.execute("SELECT * FROM quality_metrics WHERE experiment_id = ?", (experiment_id,))
    quality = cursor.fetchone()
    
    # Get geometry data
    cursor.execute("SELECT * FROM geometry_data WHERE experiment_id = ?", (experiment_id,))
    geometry = cursor.fetchone()
    
    features = []
    
    if params:
        # Process parameter features
        if params['layer_height']:
            features.append(('layer_height', params['layer_height'], 'process'))
        if params['print_speed']:
            features.append(('print_speed', params['print_speed'], 'process'))
        if params['nozzle_temperature']:
            features.append(('nozzle_temp', params['nozzle_temperature'], 'process'))
        if params['bed_temperature']:
            features.append(('bed_temp', params['bed_temperature'], 'process'))
        if params['infill_percentage']:
            features.append(('infill_pct', params['infill_percentage'], 'process'))
        
        # Derived features
        if params['nozzle_temperature'] and params['bed_temperature']:
            temp_diff = params['nozzle_temperature'] - params['bed_temperature']
            features.append(('temp_difference', temp_diff, 'derived'))
    
    if geometry:
        if geometry['volume_mm3'] and geometry['surface_area_mm2']:
            sa_vol_ratio = geometry['surface_area_mm2'] / geometry['volume_mm3'] if geometry['volume_mm3'] > 0 else 0
            features.append(('surface_area_volume_ratio', sa_vol_ratio, 'geometry'))
        if geometry['bounding_box_x'] and geometry['bounding_box_y'] and geometry['bounding_box_z']:
            aspect_ratio = max(geometry['bounding_box_x'], geometry['bounding_box_y'], geometry['bounding_box_z']) / \
                         min(geometry['bounding_box_x'], geometry['bounding_box_y'], geometry['bounding_box_z'])
            features.append(('aspect_ratio', aspect_ratio, 'geometry'))
    
    if quality:
        if quality['tensile_strength_mpa']:
            features.append(('tensile_strength', quality['tensile_strength_mpa'], 'quality'))
        if quality['surface_roughness_um']:
            features.append(('surface_roughness', quality['surface_roughness_um'], 'quality'))
        if quality['porosity_percent']:
            features.append(('porosity', quality['porosity_percent'], 'quality'))
    
    # Store features
    cursor.execute("DELETE FROM ml_features WHERE experiment_id = ?", (experiment_id,))
    for name, value, category in features:
        cursor.execute("""
            INSERT INTO ml_features (experiment_id, feature_name, feature_value, feature_category)
            VALUES (?, ?, ?, ?)
        """, (experiment_id, name, value, category))
    
    conn.commit()
    conn.close()
    
    return features

# API Routes
@app.post("/api/experiments", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate):
    """Create a new AM experiment record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert experiment
        cursor.execute("""
            INSERT INTO experiments 
            (experiment_id, experiment_name, material_type, material_batch, build_platform, 
             build_date, operator, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment.experiment_id, experiment.experiment_name, experiment.material_type,
            experiment.material_batch, experiment.build_platform, experiment.build_date,
            experiment.operator, experiment.status, experiment.notes
        ))
        
        # Insert process parameters if provided
        if experiment.process_parameters:
            params = experiment.process_parameters
            cursor.execute("""
                INSERT INTO process_parameters 
                (experiment_id, layer_height, print_speed, nozzle_temperature, bed_temperature,
                 infill_percentage, infill_pattern, shell_count, support_enabled, support_type,
                 cooling_fan_speed, retraction_distance, retraction_speed, print_time_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id, params.layer_height, params.print_speed,
                params.nozzle_temperature, params.bed_temperature, params.infill_percentage,
                params.infill_pattern, params.shell_count, params.support_enabled,
                params.support_type, params.cooling_fan_speed, params.retraction_distance,
                params.retraction_speed, params.print_time_hours
            ))
        
        # Insert geometry data if provided
        if experiment.geometry_data:
            geom = experiment.geometry_data
            cursor.execute("""
                INSERT INTO geometry_data 
                (experiment_id, part_name, stl_file_path, volume_mm3, surface_area_mm2,
                 bounding_box_x, bounding_box_y, bounding_box_z, complexity_score, support_volume_mm3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id, geom.part_name, geom.stl_file_path, geom.volume_mm3,
                geom.surface_area_mm2, geom.bounding_box_x, geom.bounding_box_y,
                geom.bounding_box_z, geom.complexity_score, geom.support_volume_mm3
            ))
        
        # Insert quality metrics if provided
        if experiment.quality_metrics:
            quality = experiment.quality_metrics
            cursor.execute("""
                INSERT INTO quality_metrics 
                (experiment_id, dimensional_accuracy_mm, surface_roughness_um, tensile_strength_mpa,
                 yield_strength_mpa, elongation_percent, density_g_per_cm3, porosity_percent,
                 hardness_hb, defect_count, defect_types, measurement_date, measurement_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id, quality.dimensional_accuracy_mm, quality.surface_roughness_um,
                quality.tensile_strength_mpa, quality.yield_strength_mpa, quality.elongation_percent,
                quality.density_g_per_cm3, quality.porosity_percent, quality.hardness_hb,
                quality.defect_count, quality.defect_types, quality.measurement_date,
                quality.measurement_method
            ))
        
        conn.commit()
        
        # Compute ML features
        compute_ml_features(experiment.experiment_id)
        
        conn.close()
        return get_experiment(experiment.experiment_id)
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Experiment ID already exists")

@app.get("/api/experiments", response_model=List[ExperimentResponse])
def list_experiments(
    material_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List experiments with optional filtering"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM experiments WHERE 1=1"
    params = []
    
    if material_type:
        query += " AND material_type = ?"
        params.append(material_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY build_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    experiments = []
    for row in rows:
        exp = dict(row)
        exp['process_parameters'] = get_process_parameters(row['experiment_id'])
        exp['geometry_data'] = get_geometry_data(row['experiment_id'])
        exp['quality_metrics'] = get_quality_metrics(row['experiment_id'])
        experiments.append(ExperimentResponse(**exp))
    
    conn.close()
    return experiments

@app.get("/api/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str):
    """Get a specific experiment by ID"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    exp = dict(row)
    exp['process_parameters'] = get_process_parameters(experiment_id)
    exp['geometry_data'] = get_geometry_data(experiment_id)
    exp['quality_metrics'] = get_quality_metrics(experiment_id)
    
    conn.close()
    return ExperimentResponse(**exp)

def get_process_parameters(experiment_id: str):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM process_parameters WHERE experiment_id = ?", (experiment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_geometry_data(experiment_id: str):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM geometry_data WHERE experiment_id = ?", (experiment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_quality_metrics(experiment_id: str):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quality_metrics WHERE experiment_id = ?", (experiment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

@app.get("/api/experiments/{experiment_id}/ml-features")
def get_ml_features(experiment_id: str):
    """Get ML-ready features for an experiment"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT feature_name, feature_value, feature_category 
        FROM ml_features 
        WHERE experiment_id = ?
    """, (experiment_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        # Compute features if they don't exist
        compute_ml_features(experiment_id)
        return get_ml_features(experiment_id)
    
    return {
        "experiment_id": experiment_id,
        "features": {row['feature_name']: row['feature_value'] for row in rows},
        "categories": {row['feature_name']: row['feature_category'] for row in rows}
    }

@app.get("/api/export/ml-dataset")
def export_ml_dataset(
    format: str = Query("csv", regex="^(csv|parquet|json)$"),
    material_type: Optional[str] = None
):
    """Export dataset in ML-ready format"""
    conn = get_db_connection()
    
    # Build comprehensive dataset
    query = """
        SELECT 
            e.experiment_id,
            e.material_type,
            e.material_batch,
            e.build_date,
            pp.layer_height,
            pp.print_speed,
            pp.nozzle_temperature,
            pp.bed_temperature,
            pp.infill_percentage,
            pp.infill_pattern,
            pp.shell_count,
            pp.support_enabled,
            pp.print_time_hours,
            gd.volume_mm3,
            gd.surface_area_mm2,
            gd.complexity_score,
            qm.tensile_strength_mpa,
            qm.yield_strength_mpa,
            qm.surface_roughness_um,
            qm.porosity_percent,
            qm.density_g_per_cm3,
            qm.defect_count
        FROM experiments e
        LEFT JOIN process_parameters pp ON e.experiment_id = pp.experiment_id
        LEFT JOIN geometry_data gd ON e.experiment_id = gd.experiment_id
        LEFT JOIN quality_metrics qm ON e.experiment_id = qm.experiment_id
    """
    
    params = []
    if material_type:
        query += " WHERE e.material_type = ?"
        params.append(material_type)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
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

@app.get("/api/analytics/summary")
def get_analytics_summary():
    """Get analytics summary of the dataset"""
    conn = get_db_connection()
    
    # Total experiments
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM experiments")
    total_experiments = cursor.fetchone()[0]
    
    # Material distribution
    cursor.execute("SELECT material_type, COUNT(*) FROM experiments GROUP BY material_type")
    material_dist = dict(cursor.fetchall())
    
    # Average quality metrics
    cursor.execute("""
        SELECT 
            AVG(tensile_strength_mpa) as avg_tensile,
            AVG(surface_roughness_um) as avg_roughness,
            AVG(porosity_percent) as avg_porosity
        FROM quality_metrics
    """)
    avg_quality = cursor.fetchone()
    
    # Process parameter ranges
    cursor.execute("""
        SELECT 
            MIN(nozzle_temperature) as min_temp,
            MAX(nozzle_temperature) as max_temp,
            AVG(nozzle_temperature) as avg_temp,
            MIN(print_speed) as min_speed,
            MAX(print_speed) as max_speed,
            AVG(print_speed) as avg_speed
        FROM process_parameters
    """)
    param_ranges = cursor.fetchone()
    
    conn.close()
    
    return {
        "total_experiments": total_experiments,
        "material_distribution": material_dist,
        "average_quality_metrics": {
            "tensile_strength_mpa": avg_quality[0],
            "surface_roughness_um": avg_quality[1],
            "porosity_percent": avg_quality[2]
        },
        "process_parameter_ranges": {
            "nozzle_temperature": {
                "min": param_ranges[0],
                "max": param_ranges[1],
                "avg": param_ranges[2]
            },
            "print_speed": {
                "min": param_ranges[3],
                "max": param_ranges[4],
                "avg": param_ranges[5]
            }
        }
    }

@app.post("/api/experiments/{experiment_id}/sensor-data")
def add_sensor_data(
    experiment_id: str,
    sensor_type: str,
    timestamp: datetime,
    value: float,
    unit: str,
    location: Optional[str] = None
):
    """Add sensor data point"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sensor_data (experiment_id, sensor_type, timestamp, value, unit, location)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (experiment_id, sensor_type, timestamp, value, unit, location))
    
    conn.commit()
    conn.close()
    
    return {"message": "Sensor data added successfully"}

@app.get("/api/experiments/{experiment_id}/sensor-data")
def get_sensor_data(experiment_id: str, sensor_type: Optional[str] = None):
    """Get sensor data for an experiment"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if sensor_type:
        cursor.execute("""
            SELECT * FROM sensor_data 
            WHERE experiment_id = ? AND sensor_type = ?
            ORDER BY timestamp
        """, (experiment_id, sensor_type))
    else:
        cursor.execute("""
            SELECT * FROM sensor_data 
            WHERE experiment_id = ?
            ORDER BY timestamp
        """, (experiment_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Serve frontend
@app.get("/")
def read_root():
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
