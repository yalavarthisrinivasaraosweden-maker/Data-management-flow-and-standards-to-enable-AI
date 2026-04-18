"""
Version Control API Endpoints
RESTful API for version control and data tracking
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import version control functions
from version_control import (
    get_db, DataVersion, VersionTag,
    create_version, restore_version, compare_versions, get_version_history,
    create_experiment_snapshot, VersionResponseModel, VersionSnapshotModel,
    VersionDiffModel, VersionHistoryModel, VersionCreateModel
)

# Import existing API
from restful_api import app

# Pydantic Models
class RestoreRequestModel(BaseModel):
    restored_by: str = Field(..., description="User restoring the version")
    create_new_version: bool = Field(True, description="Whether to create a new version for the restore")

class VersionTagModel(BaseModel):
    tag_name: str
    tag_value: Optional[str] = None

# Version Control API Endpoints

@app.post(
    "/api/v1/experiments/{experiment_id}/versions",
    response_model=VersionResponseModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Version Control"],
    summary="Create version snapshot",
    description="Create a snapshot version of the current experiment state"
)
def create_experiment_version(
    experiment_id: str = Path(..., description="Experiment ID"),
    version_data: VersionCreateModel = ...,
    db: Session = Depends(get_db)
):
    """Create a new version snapshot"""
    try:
        # Get current version
        current_version = db.query(DataVersion).filter(
            DataVersion.experiment_id == experiment_id,
            DataVersion.is_current == True
        ).first()
        
        previous_version_id = current_version.version_id if current_version else None
        
        version = create_version(
            db=db,
            experiment_id=experiment_id,
            created_by=version_data.created_by,
            change_type=version_data.change_type,
            change_description=version_data.change_description,
            tags=version_data.tags,
            previous_version_id=previous_version_id
        )
        
        return VersionResponseModel(
            version_id=version.version_id,
            experiment_id=version.experiment_id,
            version_number=version.version_number,
            version_hash=version.version_hash,
            created_by=version.created_by,
            created_at=version.created_at,
            change_description=version.change_description,
            change_type=version.change_type,
            changed_fields=version.changed_fields,
            tags=version.tags or [],
            is_current=version.is_current
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    "/api/v1/experiments/{experiment_id}/versions",
    response_model=VersionHistoryModel,
    tags=["Version Control"],
    summary="Get version history",
    description="Get complete version history for an experiment"
)
def get_experiment_versions(
    experiment_id: str = Path(..., description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """Get version history for an experiment"""
    try:
        return get_version_history(db, experiment_id)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    "/api/v1/versions/{version_id}",
    response_model=VersionSnapshotModel,
    tags=["Version Control"],
    summary="Get version snapshot",
    description="Get full snapshot data for a specific version"
)
def get_version_snapshot(
    version_id: int = Path(..., description="Version ID"),
    db: Session = Depends(get_db)
):
    """Get full snapshot for a version"""
    try:
        version = db.query(DataVersion).filter(DataVersion.version_id == version_id).first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        return VersionSnapshotModel(
            version_id=version.version_id,
            experiment_id=version.experiment_id,
            version_number=version.version_number,
            created_at=version.created_at,
            created_by=version.created_by,
            experiment=version.experiment_snapshot or {},
            process_parameters=version.process_parameters_snapshot,
            geometry_data=version.geometry_data_snapshot,
            quality_metrics=version.quality_metrics_snapshot
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post(
    "/api/v1/versions/{version_id}/restore",
    tags=["Version Control"],
    summary="Restore version",
    description="Restore an experiment to a specific version"
)
def restore_experiment_version(
    version_id: int = Path(..., description="Version ID to restore"),
    restore_data: RestoreRequestModel = ...,
    db: Session = Depends(get_db)
):
    """Restore experiment to a specific version"""
    try:
        restored_exp = restore_version(
            db=db,
            version_id=version_id,
            restored_by=restore_data.restored_by
        )
        
        return {
            "message": f"Experiment restored to version {version_id}",
            "experiment_id": restored_exp.experiment_id,
            "restored_by": restore_data.restored_by,
            "restored_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    "/api/v1/versions/{version1_id}/compare/{version2_id}",
    response_model=VersionDiffModel,
    tags=["Version Control"],
    summary="Compare versions",
    description="Compare two versions and get differences"
)
def compare_two_versions(
    version1_id: int = Path(..., description="First version ID"),
    version2_id: int = Path(..., description="Second version ID"),
    db: Session = Depends(get_db)
):
    """Compare two versions"""
    try:
        return compare_versions(db, version1_id, version2_id)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    "/api/v1/versions",
    response_model=List[VersionResponseModel],
    tags=["Version Control"],
    summary="List all versions",
    description="List all versions across all experiments with filtering"
)
def list_all_versions(
    experiment_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """List all versions with filtering"""
    try:
        query = db.query(DataVersion)
        
        if experiment_id:
            query = query.filter(DataVersion.experiment_id == experiment_id)
        if created_by:
            query = query.filter(DataVersion.created_by == created_by)
        if change_type:
            query = query.filter(DataVersion.change_type == change_type)
        if tag:
            query = query.filter(DataVersion.tags.contains([tag]))
        
        versions = query.order_by(DataVersion.created_at.desc()).offset(offset).limit(limit).all()
        
        return [VersionResponseModel(
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
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post(
    "/api/v1/versions/{version_id}/tags",
    tags=["Version Control"],
    summary="Add tag to version",
    description="Add a tag to a version for organization"
)
def add_version_tag(
    version_id: int = Path(..., description="Version ID"),
    tag_data: VersionTagModel = ...,
    db: Session = Depends(get_db)
):
    """Add tag to version"""
    try:
        version = db.query(DataVersion).filter(DataVersion.version_id == version_id).first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        tags = version.tags or []
        if tag_data.tag_name not in tags:
            tags.append(tag_data.tag_name)
            version.tags = tags
            db.commit()
        
        return {
            "message": f"Tag '{tag_data.tag_name}' added to version {version_id}",
            "version_id": version_id,
            "tags": tags
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.delete(
    "/api/v1/versions/{version_id}/tags/{tag_name}",
    tags=["Version Control"],
    summary="Remove tag from version",
    description="Remove a tag from a version"
)
def remove_version_tag(
    version_id: int = Path(..., description="Version ID"),
    tag_name: str = Path(..., description="Tag name to remove"),
    db: Session = Depends(get_db)
):
    """Remove tag from version"""
    try:
        version = db.query(DataVersion).filter(DataVersion.version_id == version_id).first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_id} not found"
            )
        
        tags = version.tags or []
        if tag_name in tags:
            tags.remove(tag_name)
            version.tags = tags
            db.commit()
        
        return {
            "message": f"Tag '{tag_name}' removed from version {version_id}",
            "version_id": version_id,
            "tags": tags
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Middleware to auto-create versions on experiment updates
@app.middleware("http")
async def auto_version_middleware(request, call_next):
    """Automatically create versions when experiments are updated"""
    # This would be integrated with the main API update endpoints
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
