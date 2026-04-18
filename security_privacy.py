"""
Data security and privacy protection system for protection and compliance.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from am_data_pipeline_postgres import Base, SessionLocal, engine, get_db
from restful_api import app


JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    # Auto-generate for local/dev usage only.
    FERNET_KEY = Fernet.generate_key().decode("utf-8")
fernet = Fernet(FERNET_KEY.encode("utf-8"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/security/token")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    username = Column(String(100), nullable=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(Integer, nullable=False)
    ip_address = Column(String(100), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    details = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Seed users from env for demo/prototype.
USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "password_hash": _hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
        "role": "admin",
        "disabled": False,
    },
    "analyst": {
        "username": "analyst",
        "password_hash": _hash_password(os.getenv("ANALYST_PASSWORD", "analyst123")),
        "role": "analyst",
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "password_hash": _hash_password(os.getenv("VIEWER_PASSWORD", "viewer123")),
        "role": "viewer",
        "disabled": False,
    },
}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserProfile(BaseModel):
    username: str
    role: str
    disabled: bool


class EncryptRequest(BaseModel):
    plaintext: str = Field(..., min_length=1)


class EncryptResponse(BaseModel):
    ciphertext: str


class DecryptRequest(BaseModel):
    ciphertext: str = Field(..., min_length=1)


class MaskRequest(BaseModel):
    record: Dict[str, Any]
    fields: Optional[List[str]] = None


class ComplianceReport(BaseModel):
    encryption_enabled: bool
    auth_enabled: bool
    audit_logging_enabled: bool
    pii_masking_available: bool
    password_policy: Dict[str, Any]
    recommendations: List[str]


def _create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


def _get_user(username: str) -> Optional[Dict[str, Any]]:
    return USERS_DB.get(username)


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username = payload.get("sub")
        if not username:
            raise credentials_exc
    except jwt.PyJWTError as exc:
        raise credentials_exc from exc

    user = _get_user(username)
    if not user or user.get("disabled"):
        raise credentials_exc
    return user


def require_roles(allowed_roles: List[str]):
    def _checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return user

    return _checker


def _mask_value(value: Any) -> Any:
    if value is None:
        return None
    s = str(value)
    if len(s) <= 2:
        return "*" * len(s)
    return s[0] + ("*" * (len(s) - 2)) + s[-1]


def mask_record(record: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    masked = dict(record)
    default_fields = {"operator", "material_batch", "notes", "email", "phone"}
    target_fields = set(fields) if fields else default_fields
    for k, v in masked.items():
        if k in target_fields:
            masked[k] = _mask_value(v)
    return masked


def _password_policy_check(password: str) -> Dict[str, bool]:
    return {
        "min_length_8": len(password) >= 8,
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_number": bool(re.search(r"[0-9]", password)),
        "has_special": bool(re.search(r"[^A-Za-z0-9]", password)),
    }


def write_audit_log(
    method: str,
    path: str,
    status_code: int,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                username=username,
                method=method,
                path=path,
                status_code=status_code,
                ip_address=ip_address,
                success=200 <= status_code < 400,
                details=details,
            )
        )
        db.commit()
    finally:
        db.close()


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    username = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "", 1)
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
            username = payload.get("sub")
        except jwt.PyJWTError:
            username = None

    write_audit_log(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        username=username,
        ip_address=request.client.host if request.client else None,
    )
    return response


@app.post("/api/v1/security/token", response_model=TokenResponse, tags=["Security"])
def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _get_user(form_data.username)
    if not user or not _verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if user.get("disabled"):
        raise HTTPException(status_code=403, detail="User is disabled")
    token = _create_access_token(user["username"], user["role"])
    return TokenResponse(access_token=token, expires_in_seconds=JWT_EXPIRE_MINUTES * 60)


@app.get("/api/v1/security/me", response_model=UserProfile, tags=["Security"])
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return UserProfile(username=user["username"], role=user["role"], disabled=user["disabled"])


@app.post("/api/v1/security/encrypt", response_model=EncryptResponse, tags=["Security"])
def encrypt_value(
    payload: EncryptRequest,
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"])),
):
    del user
    ciphertext = fernet.encrypt(payload.plaintext.encode("utf-8")).decode("utf-8")
    return EncryptResponse(ciphertext=ciphertext)


@app.post("/api/v1/security/decrypt", tags=["Security"])
def decrypt_value(
    payload: DecryptRequest,
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    try:
        plaintext = fernet.decrypt(payload.ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=400, detail="Invalid ciphertext") from exc
    return {"plaintext": plaintext}


@app.post("/api/v1/security/mask-record", tags=["Privacy"])
def mask_sensitive_record(
    payload: MaskRequest,
    user: Dict[str, Any] = Depends(require_roles(["admin", "analyst", "viewer"])),
):
    del user
    return {"masked_record": mask_record(payload.record, payload.fields)}


@app.get("/api/v1/security/compliance/check", response_model=ComplianceReport, tags=["Compliance"])
def compliance_check(user: Dict[str, Any] = Depends(require_roles(["admin", "analyst"]))):
    del user
    recommendations = []
    if JWT_SECRET == "change-this-in-production":
        recommendations.append("Set a strong JWT_SECRET in environment variables.")
    if os.getenv("FERNET_KEY") is None:
        recommendations.append("Set a persistent FERNET_KEY to avoid key rotation on restart.")
    recommendations.append("Enable HTTPS termination for all production traffic.")
    recommendations.append("Rotate credentials and keys periodically.")
    recommendations.append("Restrict CORS origins in production.")

    return ComplianceReport(
        encryption_enabled=True,
        auth_enabled=True,
        audit_logging_enabled=True,
        pii_masking_available=True,
        password_policy={
            "min_length": 8,
            "requires_uppercase": True,
            "requires_lowercase": True,
            "requires_number": True,
            "requires_special_char": True,
        },
        recommendations=recommendations,
    )


@app.get("/api/v1/security/password-policy/{password}", tags=["Security"])
def check_password_policy(
    password: str,
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    return _password_policy_check(password)


@app.get("/api/v1/security/audit-logs", tags=["Security"])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_roles(["admin"])),
):
    del user
    rows = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(max(1, min(limit, 1000)))
        .all()
    )
    return {
        "count": len(rows),
        "logs": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None, # type: ignore
                "username": r.username,
                "method": r.method,
                "path": r.path,
                "status_code": r.status_code,
                "ip_address": r.ip_address,
                "success": r.success,
                "details": r.details,
            }
            for r in rows
        ],
    }
