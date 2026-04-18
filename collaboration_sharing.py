"""
Data sharing and collaboration system.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from am_data_pipeline_postgres import Base, engine, get_db
from restful_api import app
from security_privacy import get_current_user, require_roles


class ShareRecord(Base):
    __tablename__ = "share_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(50), nullable=False)  # experiment, report, dataset
    resource_id = Column(String(100), nullable=False)
    access_level = Column(String(20), nullable=False, default="view")  # view/edit/admin
    token = Column(String(128), unique=True, nullable=False, index=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)


class CollaborationNote(Base):
    __tablename__ = "collaboration_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    edited = Column(Boolean, default=False, nullable=False)


class CollaborationActivity(Base):
    __tablename__ = "collaboration_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)  # share_created, comment_added, invite_sent...
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


Base.metadata.create_all(bind=engine)


class CreateShareRequest(BaseModel):
    resource_type: str = Field(..., pattern="^(experiment|report|dataset)$")
    resource_id: str
    access_level: str = Field("view", pattern="^(view|edit|admin)$")
    expires_in_hours: Optional[int] = Field(None, ge=1, le=24 * 30)
    metadata: Optional[Dict[str, Any]] = None


class AddCommentRequest(BaseModel):
    resource_type: str = Field(..., pattern="^(experiment|report|dataset)$")
    resource_id: str
    message: str = Field(..., min_length=1, max_length=5000)


class InviteRequest(BaseModel):
    resource_type: str = Field(..., pattern="^(experiment|report|dataset)$")
    resource_id: str
    invitee: str
    role: str = Field("viewer", pattern="^(viewer|analyst|admin)$")
    note: Optional[str] = None


def _log_activity(
    db: Session,
    resource_type: str,
    resource_id: str,
    actor: str,
    action: str,
    details: Optional[str] = None,
) -> None:
    db.add(
        CollaborationActivity(
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            action=action,
            details=details,
        )
    )
    db.commit()


@app.post("/api/v1/collab/share", tags=["Sharing & Collaboration"])
def create_share_link(
    payload: CreateShareRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    token = secrets.token_urlsafe(32)
    expires_at = None
    if payload.expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

    rec = ShareRecord(
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        access_level=payload.access_level,
        token=token,
        created_by=user["username"],
        expires_at=expires_at,
        metadata_json=str(payload.metadata) if payload.metadata else None,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    _log_activity(
        db,
        payload.resource_type,
        payload.resource_id,
        user["username"],
        "share_created",
        f"access_level={payload.access_level}",
    )

    return {
        "share_id": rec.id,
        "resource_type": rec.resource_type,
        "resource_id": rec.resource_id,
        "access_level": rec.access_level,
        "token": rec.token,
        "expires_at": rec.expires_at.isoformat() if rec.expires_at else None, # type: ignore
        "revoked": rec.revoked,
    }


@app.get("/api/v1/collab/share/resolve/{token}", tags=["Sharing & Collaboration"])
def resolve_share_token(
    token: str,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    rec = db.query(ShareRecord).filter(ShareRecord.token == token).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Share token not found")
    if rec.revoked: # type: ignore
        raise HTTPException(status_code=403, detail="Share token is revoked")
    if rec.expires_at and datetime.now(timezone.utc).replace(tzinfo=None) > rec.expires_at: # type: ignore
        raise HTTPException(status_code=403, detail="Share token expired")

    _log_activity(
        db,
        rec.resource_type, # type: ignore
        rec.resource_id, # type: ignore
        user["username"],
        "share_accessed",
        f"share_id={rec.id}",
    )

    return {
        "resource_type": rec.resource_type,
        "resource_id": rec.resource_id,
        "access_level": rec.access_level,
        "shared_by": rec.created_by,
    }


@app.post("/api/v1/collab/share/revoke/{share_id}", tags=["Sharing & Collaboration"])
def revoke_share(
    share_id: int,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    rec = db.query(ShareRecord).filter(ShareRecord.id == share_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Share record not found")

    if user["role"] != "admin" and rec.created_by != user["username"]:
        raise HTTPException(status_code=403, detail="Only owner or admin can revoke")

    rec.revoked = True # type: ignore
    db.commit()
    _log_activity(db, rec.resource_type, rec.resource_id, user["username"], "share_revoked", f"share_id={share_id}") # type: ignore
    return {"message": "Share revoked", "share_id": share_id}


@app.get("/api/v1/collab/share/list", tags=["Sharing & Collaboration"])
def list_shares(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    include_revoked: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst", "viewer"])),
):
    q = db.query(ShareRecord)
    if resource_type:
        q = q.filter(ShareRecord.resource_type == resource_type)
    if resource_id:
        q = q.filter(ShareRecord.resource_id == resource_id)
    if not include_revoked:
        q = q.filter(ShareRecord.revoked == False)  # noqa: E712
    rows = q.order_by(ShareRecord.created_at.desc()).limit(limit).all()
    if user["role"] != "admin":
        rows = [r for r in rows if r.created_by == user["username"]]
    return {
        "count": len(rows),
        "shares": [
            {
                "id": r.id,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "access_level": r.access_level,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None, # type: ignore
                "expires_at": r.expires_at.isoformat() if r.expires_at else None, # type: ignore
                "revoked": r.revoked,
            }
            for r in rows
        ],
    }


@app.post("/api/v1/collab/comment", tags=["Sharing & Collaboration"])
def add_comment(
    payload: AddCommentRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst", "viewer"])),
):
    note = CollaborationNote(
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        author=user["username"],
        message=payload.message,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    _log_activity(
        db,
        payload.resource_type,
        payload.resource_id,
        user["username"],
        "comment_added",
        f"comment_id={note.id}",
    )
    return {
        "comment_id": note.id,
        "resource_type": note.resource_type,
        "resource_id": note.resource_id,
        "author": note.author,
        "message": note.message,
        "created_at": note.created_at.isoformat() if note.created_at else None, # type: ignore
    }


@app.get("/api/v1/collab/comments", tags=["Sharing & Collaboration"])
def list_comments(
    resource_type: str = Query(..., pattern="^(experiment|report|dataset)$"),
    resource_id: str = Query(...),
    limit: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst", "viewer"])),
):
    del user
    rows = (
        db.query(CollaborationNote)
        .filter(
            CollaborationNote.resource_type == resource_type,
            CollaborationNote.resource_id == resource_id,
        )
        .order_by(CollaborationNote.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(rows),
        "comments": [
            {
                "id": r.id,
                "author": r.author,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None, # type: ignore
                "edited": r.edited,
            }
            for r in rows
        ],
    }


@app.post("/api/v1/collab/invite", tags=["Sharing & Collaboration"])
def create_invite(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    # Lightweight invite model: represented as activity entry.
    detail = f"invitee={payload.invitee}, role={payload.role}, note={payload.note or ''}"
    _log_activity(
        db,
        payload.resource_type,
        payload.resource_id,
        user["username"],
        "invite_sent",
        detail,
    )
    return {
        "message": "Invite recorded",
        "resource_type": payload.resource_type,
        "resource_id": payload.resource_id,
        "invitee": payload.invitee,
        "role": payload.role,
    }


@app.get("/api/v1/collab/activity", tags=["Sharing & Collaboration"])
def activity_feed(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=5000),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst", "viewer"])),
):
    del user
    q = db.query(CollaborationActivity)
    if resource_type:
        q = q.filter(CollaborationActivity.resource_type == resource_type)
    if resource_id:
        q = q.filter(CollaborationActivity.resource_id == resource_id)
    rows = q.order_by(CollaborationActivity.created_at.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "activities": [
            {
                "id": r.id,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "actor": r.actor,
                "action": r.action,
                "details": r.details,
                "created_at": r.created_at.isoformat() if r.created_at else None, # type: ignore
            }
            for r in rows
        ],
    }
