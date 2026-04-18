"""
Version Control System for AM Experimental Data
Tracks changes, enables version history, comparison, and rollback
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json
import hashlib
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError

# Import existing models
from am_data_pipeline_postgres import (
    get_db, Experiment, ProcessParameter,
    GeometryData as GeometryDataModel,
    QualityMetric, Base as ExistingBase
)

# Version Control Database Models
Base = ExistingBase  # Use same base as existing models

class DataVersion(Base):
    """Stores version snapshots of experiments"""
    __tablename__ = "data_versions"
    
    version_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    version_hash = Column(String, nullable=False, index=True)  # Hash of the data snapshot
    created_by = Column(String, nullable=False)  # User who created this version
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    change_description = Column(Text)  # Description of what changed
    change_type = Column(String)  # 'create', 'update', 'delete', 'restore'
    
    # Snapshot data stored as JSON
    experiment_snapshot = Column(JSON)  # Full experiment data snapshot
    process_parameters_snapshot = Column(JSON)
    geometry_data_snapshot = Column(JSON)
    quality_metrics_snapshot = Column(JSON)
    
    # Metadata about what changed
    changed_fields = Column(JSON)  # List of field names that changed
    previous_version_id = Column(Integer, ForeignKey("data_versions.version_id"))
    
    # Tags and labels
    tags = Column(JSON)  # List of tags for organization
    is_current = Column(Boolean, default=False)  # Whether this is the current version
    
    __table_args__ = (
        Index('idx_version_exp', 'experiment_id'),
        Index('idx_version_number', 'experiment_id', 'version_number'),
        Index('idx_version_hash', 'version_hash'),
    )

class VersionTag(Base):
    """Tags for organizing versions"""
    __tablename__ = "version_tags"
    
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("data_versions.version_id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String, nullable=False)
    tag_value = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_tag_version', 'version_id'),
        Index('idx_tag_name', 'tag_name'),
    )

# Initialize database tables
def init_version_control_tables():
    """Create version control tables"""
    from am_data_pipeline_postgres import engine
    Base.metadata.create_all(bind=engine)

# Pydantic Models
class VersionCreateModel(BaseModel):
    change_description: Optional[str] = Field(None, description="Description of changes")
    change_type: str = Field(..., description="Type of change: create, update, delete, restore")
    created_by: str = Field(..., description="User creating this version")
    tags: Optional[List[str]] = Field(None, description="Tags for organization")

class VersionResponseModel(BaseModel):
    version_id: int
    experiment_id: str
    version_number: int
    version_hash: str
    created_by: str
    created_at: datetime
    change_description: Optional[str]
    change_type: str
    changed_fields: Optional[List[str]]
    tags: Optional[List[str]]
    is_current: bool
    
    class Config:
        from_attributes = True

class VersionSnapshotModel(BaseModel):
    """Full snapshot of experiment data at a version"""
    version_id: int
    experiment_id: str
    version_number: int
    created_at: datetime
    created_by: str
    experiment: Dict[str, Any]
    process_parameters: Optional[Dict[str, Any]]
    geometry_data: Optional[Dict[str, Any]]
    quality_metrics: Optional[Dict[str, Any]]

class VersionDiffModel(BaseModel):
    """Difference between two versions"""
    version1_id: int
    version2_id: int
    experiment_id: str
    differences: Dict[str, Dict[str, Any]]  # Field name -> {old_value, new_value}
    added_fields: List[str]
    removed_fields: List[str]
    modified_fields: List[str]

class VersionHistoryModel(BaseModel):
    """Version history for an experiment"""
    experiment_id: str
    total_versions: int
    current_version: int
    versions: List[VersionResponseModel]

# Helper Functions
def calculate_data_hash(data: Dict[str, Any]) -> str:
    """Calculate hash of data snapshot"""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()

def create_experiment_snapshot(db: Session, experiment_id: str) -> Dict[str, Any]:
    """Create a snapshot of current experiment state"""
    exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    snapshot = {
        "experiment_id": exp.experiment_id,
        "experiment_name": exp.experiment_name,
        "material_type": exp.material_type,
        "material_batch": exp.material_batch,
        "build_platform": exp.build_platform,
        "build_date": exp.build_date.isoformat() if exp.build_date else None,
        "operator": exp.operator,
        "status": exp.status,
        "notes": exp.notes,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
    }
    
    if exp.process_parameters:
        snapshot["process_parameters"] = {
            "layer_height": exp.process_parameters.layer_height,
            "print_speed": exp.process_parameters.print_speed,
            "nozzle_temperature": exp.process_parameters.nozzle_temperature,
            "bed_temperature": exp.process_parameters.bed_temperature,
            "infill_percentage": exp.process_parameters.infill_percentage,
            "infill_pattern": exp.process_parameters.infill_pattern,
            "shell_count": exp.process_parameters.shell_count,
            "support_enabled": exp.process_parameters.support_enabled,
            "support_type": exp.process_parameters.support_type,
            "cooling_fan_speed": exp.process_parameters.cooling_fan_speed,
            "retraction_distance": exp.process_parameters.retraction_distance,
            "retraction_speed": exp.process_parameters.retraction_speed,
            "print_time_hours": exp.process_parameters.print_time_hours,
        }
    
    if exp.geometry_data:
        snapshot["geometry_data"] = {
            "part_name": exp.geometry_data.part_name,
            "stl_file_path": exp.geometry_data.stl_file_path,
            "volume_mm3": exp.geometry_data.volume_mm3,
            "surface_area_mm2": exp.geometry_data.surface_area_mm2,
            "bounding_box_x": exp.geometry_data.bounding_box_x,
            "bounding_box_y": exp.geometry_data.bounding_box_y,
            "bounding_box_z": exp.geometry_data.bounding_box_z,
            "complexity_score": exp.geometry_data.complexity_score,
            "support_volume_mm3": exp.geometry_data.support_volume_mm3,
        }
    
    if exp.quality_metrics:
        snapshot["quality_metrics"] = {
            "dimensional_accuracy_mm": exp.quality_metrics.dimensional_accuracy_mm,
            "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
            "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
            "yield_strength_mpa": exp.quality_metrics.yield_strength_mpa,
            "elongation_percent": exp.quality_metrics.elongation_percent,
            "density_g_per_cm3": exp.quality_metrics.density_g_per_cm3,
            "porosity_percent": exp.quality_metrics.porosity_percent,
            "hardness_hb": exp.quality_metrics.hardness_hb,
            "defect_count": exp.quality_metrics.defect_count,
            "defect_types": exp.quality_metrics.defect_types,
            "measurement_date": exp.quality_metrics.measurement_date.isoformat() if exp.quality_metrics.measurement_date else None,
            "measurement_method": exp.quality_metrics.measurement_method,
        }
    
    return snapshot

def get_changed_fields(old_snapshot: Dict, new_snapshot: Dict) -> List[str]:
    """Compare two snapshots and return list of changed fields"""
    changed = []
    
    def compare_dicts(old: Dict, new: Dict, prefix: str = ""):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            full_key = f"{prefix}.{key}" if prefix else key
            old_val = old.get(key)
            new_val = new.get(key)
            
            if isinstance(old_val, dict) and isinstance(new_val, dict):
                compare_dicts(old_val, new_val, full_key)
            elif old_val != new_val:
                changed.append(full_key)
    
    compare_dicts(old_snapshot, new_snapshot)
    return changed

def create_version(
    db: Session,
    experiment_id: str,
    created_by: str,
    change_type: str,
    change_description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    previous_version_id: Optional[int] = None
) -> DataVersion:
    """Create a new version snapshot"""
    # Get current version number
    max_version = db.query(func.max(DataVersion.version_number)).filter(
        DataVersion.experiment_id == experiment_id
    ).scalar() or 0
    
    version_number = max_version + 1
    
    # Create snapshot
    snapshot = create_experiment_snapshot(db, experiment_id)
    
    # Calculate hash
    version_hash = calculate_data_hash(snapshot)
    
    # Check if this version already exists (same hash)
    existing = db.query(DataVersion).filter(
        DataVersion.experiment_id == experiment_id,
        DataVersion.version_hash == version_hash
    ).first()
    
    if existing:
        return existing  # Return existing version if data hasn't changed
    
    # Get changed fields if previous version exists
    changed_fields = []
    if previous_version_id:
        prev_version = db.query(DataVersion).filter(DataVersion.version_id == previous_version_id).first()
        if prev_version and prev_version.experiment_snapshot:
            changed_fields = get_changed_fields(prev_version.experiment_snapshot, snapshot)
    
    # Mark all previous versions as not current
    db.query(DataVersion).filter(
        DataVersion.experiment_id == experiment_id
    ).update({"is_current": False})
    
    # Create new version
    version = DataVersion(
        experiment_id=experiment_id,
        version_number=version_number,
        version_hash=version_hash,
        created_by=created_by,
        change_description=change_description,
        change_type=change_type,
        experiment_snapshot=snapshot,
        process_parameters_snapshot=snapshot.get("process_parameters"),
        geometry_data_snapshot=snapshot.get("geometry_data"),
        quality_metrics_snapshot=snapshot.get("quality_metrics"),
        changed_fields=changed_fields,
        previous_version_id=previous_version_id,
        tags=tags or [],
        is_current=True
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return version

def restore_version(db: Session, version_id: int, restored_by: str) -> Experiment:
    """Restore an experiment to a specific version"""
    version = db.query(DataVersion).filter(DataVersion.version_id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    exp = db.query(Experiment).filter(Experiment.experiment_id == version.experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    snapshot = version.experiment_snapshot
    
    # Restore experiment fields
    exp.experiment_name = snapshot.get("experiment_name")
    exp.material_type = snapshot.get("material_type")
    exp.material_batch = snapshot.get("material_batch")
    exp.build_platform = snapshot.get("build_platform")
    exp.build_date = datetime.fromisoformat(snapshot["build_date"]) if snapshot.get("build_date") else None
    exp.operator = snapshot.get("operator")
    exp.status = snapshot.get("status")
    exp.notes = snapshot.get("notes")
    exp.updated_at = datetime.now()
    
    # Restore process parameters
    if version.process_parameters_snapshot:
        if not exp.process_parameters:
            exp.process_parameters = ProcessParameter(experiment_id=exp.experiment_id)
        pp_data = version.process_parameters_snapshot
        for key, value in pp_data.items():
            setattr(exp.process_parameters, key, value)
    
    # Restore geometry data
    if version.geometry_data_snapshot:
        if not exp.geometry_data:
            exp.geometry_data = GeometryDataModel(experiment_id=exp.experiment_id)
        gd_data = version.geometry_data_snapshot
        for key, value in gd_data.items():
            setattr(exp.geometry_data, key, value)
    
    # Restore quality metrics
    if version.quality_metrics_snapshot:
        if not exp.quality_metrics:
            exp.quality_metrics = QualityMetric(experiment_id=exp.experiment_id)
        qm_data = version.quality_metrics_snapshot
        for key, value in qm_data.items():
            if key == "measurement_date" and value:
                setattr(exp.quality_metrics, key, datetime.fromisoformat(value))
            else:
                setattr(exp.quality_metrics, key, value)
    
    db.commit()
    db.refresh(exp)
    
    # Create a new version for the restore action
    create_version(
        db=db,
        experiment_id=exp.experiment_id,
        created_by=restored_by,
        change_type="restore",
        change_description=f"Restored to version {version.version_number}",
        previous_version_id=version_id
    )
    
    return exp

def compare_versions(db: Session, version1_id: int, version2_id: int) -> VersionDiffModel:
    """Compare two versions and return differences"""
    v1 = db.query(DataVersion).filter(DataVersion.version_id == version1_id).first()
    v2 = db.query(DataVersion).filter(DataVersion.version_id == version2_id).first()
    
    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    if v1.experiment_id != v2.experiment_id:
        raise HTTPException(status_code=400, detail="Cannot compare versions from different experiments")
    
    snapshot1 = v1.experiment_snapshot or {}
    snapshot2 = v2.experiment_snapshot or {}
    
    differences = {}
    added_fields = []
    removed_fields = []
    modified_fields = []
    
    def compare_dicts(old: Dict, new: Dict, prefix: str = ""):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            full_key = f"{prefix}.{key}" if prefix else key
            old_val = old.get(key)
            new_val = new.get(key)
            
            if key not in old:
                added_fields.append(full_key)
                differences[full_key] = {"old_value": None, "new_value": new_val}
            elif key not in new:
                removed_fields.append(full_key)
                differences[full_key] = {"old_value": old_val, "new_value": None}
            elif isinstance(old_val, dict) and isinstance(new_val, dict):
                compare_dicts(old_val, new_val, full_key)
            elif old_val != new_val:
                modified_fields.append(full_key)
                differences[full_key] = {"old_value": old_val, "new_value": new_val}
    
    compare_dicts(snapshot1, snapshot2)
    
    return VersionDiffModel(
        version1_id=version1_id,
        version2_id=version2_id,
        experiment_id=v1.experiment_id,
        differences=differences,
        added_fields=added_fields,
        removed_fields=removed_fields,
        modified_fields=modified_fields
    )

# API Routes (to be integrated with main API)
def get_version_history(db: Session, experiment_id: str) -> VersionHistoryModel:
    """Get version history for an experiment"""
    versions = db.query(DataVersion).filter(
        DataVersion.experiment_id == experiment_id
    ).order_by(DataVersion.version_number.desc()).all()
    
    current_version = db.query(DataVersion).filter(
        DataVersion.experiment_id == experiment_id,
        DataVersion.is_current == True
    ).first()
    
    return VersionHistoryModel(
        experiment_id=experiment_id,
        total_versions=len(versions),
        current_version=current_version.version_number if current_version else 0,
        versions=[VersionResponseModel(
            version_id=v.version_id,
            experiment_id=v.experiment_id,
            version_number=v.version_number,
            version_hash=v.version_hash,
            created_by=v.created_by,
            created_at=v.created_at,
            change_description=v.change_description,
            change_type=v.change_type,
            changed_fields=v.changed_fields,
            tags=v.tags or [],
            is_current=v.is_current
        ) for v in versions]
    )

# Initialize tables
init_version_control_tables()
