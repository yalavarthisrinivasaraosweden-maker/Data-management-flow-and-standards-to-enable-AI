"""
AM Experimental Data Management Pipeline - MongoDB Version
Robust data storage system with MongoDB database
"""

from fastapi import FastAPI, HTTPException, Query
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

# MongoDB imports
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

# Database configuration
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://localhost:27017/"
)
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "am_data_db")

# Create MongoDB client with connection pooling
client = MongoClient(
    MONGODB_URL,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000
)

db = client[DATABASE_NAME]

# Create indexes for efficient queries
def init_indexes():
    """Create database indexes"""
    try:
        # Experiments collection indexes
        db.experiments.create_index("experiment_id", unique=True)
        db.experiments.create_index("material_type")
        db.experiments.create_index("build_date")
        db.experiments.create_index("status")
        
        # Sensor data indexes
        db.sensor_data.create_index("experiment_id")
        db.sensor_data.create_index("sensor_type")
        db.sensor_data.create_index("timestamp")
        db.sensor_data.create_index([("experiment_id", 1), ("timestamp", 1)])
        
        # ML features indexes
        db.ml_features.create_index("experiment_id")
        db.ml_features.create_index("feature_name")
        db.ml_features.create_index([("experiment_id", 1), ("feature_name", 1)])
        
        print("✓ MongoDB indexes created successfully")
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")

# Initialize indexes
try:
    client.admin.command('ping')
    init_indexes()
    print("✓ Connected to MongoDB successfully")
except ConnectionFailure:
    print("✗ Failed to connect to MongoDB. Please ensure MongoDB is running.")

app = FastAPI(title="AM Experimental Data Management Pipeline - MongoDB")

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
def compute_ml_features(experiment_id: str, experiment_data: dict):
    """Compute ML-ready features from experiment data"""
    features = []
    
    # Process parameter features
    if experiment_data.get('process_parameters'):
        pp = experiment_data['process_parameters']
        if pp.get('layer_height'):
            features.append({'feature_name': 'layer_height', 'feature_value': pp['layer_height'], 'feature_category': 'process'})
        if pp.get('print_speed'):
            features.append({'feature_name': 'print_speed', 'feature_value': pp['print_speed'], 'feature_category': 'process'})
        if pp.get('nozzle_temperature'):
            features.append({'feature_name': 'nozzle_temp', 'feature_value': pp['nozzle_temperature'], 'feature_category': 'process'})
        if pp.get('bed_temperature'):
            features.append({'feature_name': 'bed_temp', 'feature_value': pp['bed_temperature'], 'feature_category': 'process'})
        if pp.get('infill_percentage'):
            features.append({'feature_name': 'infill_pct', 'feature_value': pp['infill_percentage'], 'feature_category': 'process'})
        
        # Derived features
        if pp.get('nozzle_temperature') and pp.get('bed_temperature'):
            temp_diff = pp['nozzle_temperature'] - pp['bed_temperature']
            features.append({'feature_name': 'temp_difference', 'feature_value': temp_diff, 'feature_category': 'derived'})
    
    # Geometry features
    if experiment_data.get('geometry_data'):
        gd = experiment_data['geometry_data']
        if gd.get('volume_mm3') and gd.get('surface_area_mm2') and gd['volume_mm3'] > 0:
            sa_vol_ratio = gd['surface_area_mm2'] / gd['volume_mm3']
            features.append({'feature_name': 'surface_area_volume_ratio', 'feature_value': sa_vol_ratio, 'feature_category': 'geometry'})
        if gd.get('bounding_box_x') and gd.get('bounding_box_y') and gd.get('bounding_box_z'):
            dims = [gd['bounding_box_x'], gd['bounding_box_y'], gd['bounding_box_z']]
            aspect_ratio = max(dims) / min(dims) if min(dims) > 0 else 0
            features.append({'feature_name': 'aspect_ratio', 'feature_value': aspect_ratio, 'feature_category': 'geometry'})
    
    # Quality features
    if experiment_data.get('quality_metrics'):
        qm = experiment_data['quality_metrics']
        if qm.get('tensile_strength_mpa'):
            features.append({'feature_name': 'tensile_strength', 'feature_value': qm['tensile_strength_mpa'], 'feature_category': 'quality'})
        if qm.get('surface_roughness_um'):
            features.append({'feature_name': 'surface_roughness', 'feature_value': qm['surface_roughness_um'], 'feature_category': 'quality'})
        if qm.get('porosity_percent'):
            features.append({'feature_name': 'porosity', 'feature_value': qm['porosity_percent'], 'feature_category': 'quality'})
    
    # Store features
    if features:
        db.ml_features.delete_many({'experiment_id': experiment_id})
        for feature in features:
            feature['experiment_id'] = experiment_id
            feature['computed_at'] = datetime.now()
        db.ml_features.insert_many(features)
    
    return features

# API Routes
@app.post("/api/experiments", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate):
    """Create a new AM experiment record"""
    try:
        # Check if experiment already exists
        existing = db.experiments.find_one({"experiment_id": experiment.experiment_id})
        if existing:
            raise HTTPException(status_code=400, detail="Experiment ID already exists")
        
        # Prepare experiment document
        experiment_doc = {
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.experiment_name,
            "material_type": experiment.material_type,
            "material_batch": experiment.material_batch,
            "build_platform": experiment.build_platform,
            "build_date": experiment.build_date,
            "operator": experiment.operator,
            "status": experiment.status,
            "notes": experiment.notes,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add nested documents
        if experiment.process_parameters:
            experiment_doc["process_parameters"] = experiment.process_parameters.dict(exclude_none=True)
        if experiment.geometry_data:
            experiment_doc["geometry_data"] = experiment.geometry_data.dict(exclude_none=True)
        if experiment.quality_metrics:
            qm_dict = experiment.quality_metrics.dict(exclude_none=True)
            if qm_dict.get('measurement_date'):
                qm_dict['measurement_date'] = qm_dict['measurement_date']
            experiment_doc["quality_metrics"] = qm_dict
        
        # Insert experiment
        db.experiments.insert_one(experiment_doc)
        
        # Compute ML features
        compute_ml_features(experiment.experiment_id, experiment_doc)
        
        # Return created experiment
        return get_experiment(experiment.experiment_id)
        
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Experiment ID already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments", response_model=List[ExperimentResponse])
def list_experiments(
    material_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List experiments with optional filtering"""
    try:
        query = {}
        if material_type:
            query["material_type"] = material_type
        if status:
            query["status"] = status
        
        experiments = db.experiments.find(query).sort("build_date", -1).skip(offset).limit(limit)
        
        result = []
        for exp in experiments:
            result.append(ExperimentResponse(
                experiment_id=exp["experiment_id"],
                experiment_name=exp["experiment_name"],
                material_type=exp.get("material_type"),
                material_batch=exp.get("material_batch"),
                build_platform=exp.get("build_platform"),
                build_date=exp.get("build_date"),
                operator=exp.get("operator"),
                status=exp.get("status", "completed"),
                notes=exp.get("notes"),
                created_at=exp.get("created_at", datetime.now()),
                updated_at=exp.get("updated_at", datetime.now()),
                process_parameters=ProcessParameters(**exp["process_parameters"]) if exp.get("process_parameters") else None,
                geometry_data=GeometryData(**exp["geometry_data"]) if exp.get("geometry_data") else None,
                quality_metrics=QualityMetrics(**exp["quality_metrics"]) if exp.get("quality_metrics") else None
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str):
    """Get a specific experiment by ID"""
    try:
        exp = db.experiments.find_one({"experiment_id": experiment_id})
        
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return ExperimentResponse(
            experiment_id=exp["experiment_id"],
            experiment_name=exp["experiment_name"],
            material_type=exp.get("material_type"),
            material_batch=exp.get("material_batch"),
            build_platform=exp.get("build_platform"),
            build_date=exp.get("build_date"),
            operator=exp.get("operator"),
            status=exp.get("status", "completed"),
            notes=exp.get("notes"),
            created_at=exp.get("created_at", datetime.now()),
            updated_at=exp.get("updated_at", datetime.now()),
            process_parameters=ProcessParameters(**exp["process_parameters"]) if exp.get("process_parameters") else None,
            geometry_data=GeometryData(**exp["geometry_data"]) if exp.get("geometry_data") else None,
            quality_metrics=QualityMetrics(**exp["quality_metrics"]) if exp.get("quality_metrics") else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}/ml-features")
def get_ml_features(experiment_id: str):
    """Get ML-ready features for an experiment"""
    try:
        features = list(db.ml_features.find({"experiment_id": experiment_id}))
        
        if not features:
            # Get experiment and compute features
            exp = db.experiments.find_one({"experiment_id": experiment_id})
            if exp:
                compute_ml_features(experiment_id, exp)
                features = list(db.ml_features.find({"experiment_id": experiment_id}))
        
        return {
            "experiment_id": experiment_id,
            "features": {f["feature_name"]: f["feature_value"] for f in features},
            "categories": {f["feature_name"]: f["feature_category"] for f in features}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/export/ml-dataset")
def export_ml_dataset(
    format: str = Query("csv", regex="^(csv|parquet|json)$"),
    material_type: Optional[str] = None
):
    """Export dataset in ML-ready format"""
    try:
        # Build aggregation pipeline
        pipeline = [
            {"$match": {"material_type": material_type}} if material_type else {"$match": {}},
            {
                "$lookup": {
                    "from": "experiments",
                    "localField": "experiment_id",
                    "foreignField": "experiment_id",
                    "as": "experiment"
                }
            },
            {"$unwind": "$experiment"},
            {
                "$project": {
                    "experiment_id": "$experiment.experiment_id",
                    "material_type": "$experiment.material_type",
                    "material_batch": "$experiment.material_batch",
                    "build_date": "$experiment.build_date",
                    "layer_height": "$experiment.process_parameters.layer_height",
                    "print_speed": "$experiment.process_parameters.print_speed",
                    "nozzle_temperature": "$experiment.process_parameters.nozzle_temperature",
                    "bed_temperature": "$experiment.process_parameters.bed_temperature",
                    "infill_percentage": "$experiment.process_parameters.infill_percentage",
                    "infill_pattern": "$experiment.process_parameters.infill_pattern",
                    "shell_count": "$experiment.process_parameters.shell_count",
                    "support_enabled": "$experiment.process_parameters.support_enabled",
                    "print_time_hours": "$experiment.process_parameters.print_time_hours",
                    "volume_mm3": "$experiment.geometry_data.volume_mm3",
                    "surface_area_mm2": "$experiment.geometry_data.surface_area_mm2",
                    "complexity_score": "$experiment.geometry_data.complexity_score",
                    "tensile_strength_mpa": "$experiment.quality_metrics.tensile_strength_mpa",
                    "yield_strength_mpa": "$experiment.quality_metrics.yield_strength_mpa",
                    "surface_roughness_um": "$experiment.quality_metrics.surface_roughness_um",
                    "porosity_percent": "$experiment.quality_metrics.porosity_percent",
                    "density_g_per_cm3": "$experiment.quality_metrics.density_g_per_cm3",
                    "defect_count": "$experiment.quality_metrics.defect_count"
                }
            }
        ]
        
        # Get all experiments and convert to DataFrame
        experiments = list(db.experiments.find({} if not material_type else {"material_type": material_type}))
        
        # Convert to DataFrame
        records = []
        for exp in experiments:
            record = {
                "experiment_id": exp["experiment_id"],
                "material_type": exp.get("material_type"),
                "material_batch": exp.get("material_batch"),
                "build_date": exp.get("build_date"),
            }
            
            if exp.get("process_parameters"):
                record.update({f"pp_{k}": v for k, v in exp["process_parameters"].items()})
            
            if exp.get("geometry_data"):
                record.update({f"geom_{k}": v for k, v in exp["geometry_data"].items()})
            
            if exp.get("quality_metrics"):
                record.update({f"qm_{k}": v for k, v in exp["quality_metrics"].items()})
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Flatten column names
        df.columns = [col.replace("pp_", "").replace("geom_", "").replace("qm_", "") for col in df.columns]
        
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
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/analytics/summary")
def get_analytics_summary():
    """Get analytics summary of the dataset"""
    try:
        # Total experiments
        total_experiments = db.experiments.count_documents({})
        
        # Material distribution
        material_pipeline = [
            {"$match": {"material_type": {"$ne": None}}},
            {"$group": {"_id": "$material_type", "count": {"$sum": 1}}}
        ]
        material_dist = {item["_id"]: item["count"] for item in db.experiments.aggregate(material_pipeline)}
        
        # Average quality metrics
        quality_pipeline = [
            {"$match": {"quality_metrics": {"$exists": True}}},
            {
                "$group": {
                    "_id": None,
                    "avg_tensile": {"$avg": "$quality_metrics.tensile_strength_mpa"},
                    "avg_roughness": {"$avg": "$quality_metrics.surface_roughness_um"},
                    "avg_porosity": {"$avg": "$quality_metrics.porosity_percent"}
                }
            }
        ]
        avg_quality = list(db.experiments.aggregate(quality_pipeline))
        avg_quality = avg_quality[0] if avg_quality else {}
        
        # Process parameter ranges
        param_pipeline = [
            {"$match": {"process_parameters": {"$exists": True}}},
            {
                "$group": {
                    "_id": None,
                    "min_temp": {"$min": "$process_parameters.nozzle_temperature"},
                    "max_temp": {"$max": "$process_parameters.nozzle_temperature"},
                    "avg_temp": {"$avg": "$process_parameters.nozzle_temperature"},
                    "min_speed": {"$min": "$process_parameters.print_speed"},
                    "max_speed": {"$max": "$process_parameters.print_speed"},
                    "avg_speed": {"$avg": "$process_parameters.print_speed"}
                }
            }
        ]
        param_ranges = list(db.experiments.aggregate(param_pipeline))
        param_ranges = param_ranges[0] if param_ranges else {}
        
        return {
            "total_experiments": total_experiments,
            "material_distribution": material_dist,
            "average_quality_metrics": {
                "tensile_strength_mpa": avg_quality.get("avg_tensile"),
                "surface_roughness_um": avg_quality.get("avg_roughness"),
                "porosity_percent": avg_quality.get("avg_porosity")
            },
            "process_parameter_ranges": {
                "nozzle_temperature": {
                    "min": param_ranges.get("min_temp"),
                    "max": param_ranges.get("max_temp"),
                    "avg": param_ranges.get("avg_temp")
                },
                "print_speed": {
                    "min": param_ranges.get("min_speed"),
                    "max": param_ranges.get("max_speed"),
                    "avg": param_ranges.get("avg_speed")
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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
    try:
        # Verify experiment exists
        exp = db.experiments.find_one({"experiment_id": experiment_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        sensor_data = {
            "experiment_id": experiment_id,
            "sensor_type": sensor_type,
            "timestamp": timestamp,
            "value": value,
            "unit": unit,
            "location": location
        }
        db.sensor_data.insert_one(sensor_data)
        
        return {"message": "Sensor data added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/experiments/{experiment_id}/sensor-data")
def get_sensor_data(experiment_id: str, sensor_type: Optional[str] = None):
    """Get sensor data for an experiment"""
    try:
        query = {"experiment_id": experiment_id}
        if sensor_type:
            query["sensor_type"] = sensor_type
        
        sensor_data = list(db.sensor_data.find(query).sort("timestamp", 1))
        
        return [{
            "sensor_id": str(sd["_id"]),
            "experiment_id": sd["experiment_id"],
            "sensor_type": sd["sensor_type"],
            "timestamp": sd["timestamp"].isoformat() if sd.get("timestamp") else None,
            "value": sd["value"],
            "unit": sd["unit"],
            "location": sd.get("location")
        } for sd in sensor_data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "database_type": "MongoDB",
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
