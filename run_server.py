"""
Clean startup file for the AM Data Pipeline.
Avoids chained import failures from extension modules.
Run this instead of api_server.py
"""

import uvicorn
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session, configure_mappers
from datetime import datetime

# ── Step 1: import all database models FIRST ──────────────────────────────
# This ensures every ORM class is registered before configure_mappers runs
from am_data_pipeline_postgres import (
    engine, get_db,
    Experiment, ProcessParameter, GeometryData,
    QualityMetric, SensorData, MLFeature
)

# ── Step 2: force SQLAlchemy to resolve all string-based relationships now ─
# This prevents "failed to locate a name" errors on first request
try:
    configure_mappers()
    print("[OK]   SQLAlchemy mappers configured successfully")
except Exception as e:
    print(f"[WARN] configure_mappers warning: {e}")

# ── Step 3: import the core FastAPI app ───────────────────────────────────
from restful_api import app

# ── Step 4: safely import each extension module ───────────────────────────
modules_loaded = []
modules_failed = []

for module_name in [
    "version_control_api",
    "data_quality_api",
    "data_analysis_api",
    "ml_api",
    "security_privacy",
    "backup_recovery",
    "collaboration_sharing",
]:
    try:
        __import__(module_name)
        modules_loaded.append(module_name)
    except Exception as e:
        modules_failed.append((module_name, str(e)))

print("\n=== Module load report ===")
for m in modules_loaded:
    print(f"  [OK]   {m}")
for m, err in modules_failed:
    print(f"  [SKIP] {m} — {err[:100]}")
print("==========================\n")

# ── Step 5: register guaranteed endpoints ────────────────────────────────

@app.get("/api/v1/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "modules_loaded": modules_loaded,
            "modules_skipped": [m for m, _ in modules_failed],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.get("/dashboard/basic")
def basic_dashboard():
    return FileResponse("am_dashboard.html")

@app.get("/dashboard/advanced")
def advanced_dashboard():
    return FileResponse("am_dashboard_advanced.html")

# ── Step 6: start the server ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting AM Data Pipeline API...")
    print("  Swagger docs : http://localhost:8000/api/v1/docs")
    print("  Health check : http://localhost:8000/api/v1/health")
    print("  Dashboard    : http://localhost:8000")
    print("  Advanced UI  : http://localhost:8000/dashboard/advanced\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)