# Data Management Flow and Standards to Enable AI
### A FAIR-Compliant Pipeline for Additive Manufacturing Experimental Data

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![University West](https://img.shields.io/badge/University-West%2C%20Sweden-darkblue)](https://www.hv.se)
[![GKN Aerospace](https://img.shields.io/badge/Partner-GKN%20Aerospace-orange)](https://www.gknaerospace.com)

---

> **Master's Thesis Project — AI and Automation Programme, University West, 2026**
>
> **Authors:**  Srinivasa Rao Yalavarthi . Akshayakumar Srinivasan
>
> **Industrial Partner:** GKN Aerospace, Trollhättan, Sweden
>
> **Supervisors:** Prof. Amit Kumar Mishra
>
> **Examiner:** Dr. Yongcui Mi

---

## Table of Contents

- [Project Overview](#project-overview)
- [Research Questions](#research-questions)
- [Key Results](#key-results)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Frontend Interfaces](#frontend-interfaces)
- [ML Pipeline Usage](#ml-pipeline-usage)
- [Compression Benchmarking](#compression-benchmarking)
- [Data Quality & FAIR Compliance](#data-quality--fair-compliance)
- [Version Control](#version-control)
- [Docker Deployment](#docker-deployment)
- [Running the Tests (ATPs)](#running-the-tests-atps)
- [Dataset & Reproducibility](#dataset--reproducibility)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Project Overview

Modern Additive Manufacturing (AM) processes at GKN Aerospace produce large volumes of experimental data across heterogeneous sources: LPBF machine logs, thermographic sensor streams (HDF5), tensile test CSVs, and Excel quality reports. This data exists in incompatible formats, with no standardised column names, no version control, and no FAIR-compliant metadata — making it unusable by AI/ML systems without days of manual preparation.

This project designs, implements, and validates a **five-layer FAIR-compliant data management pipeline** that:

- **Ingests** data from 6 file formats and 5+ machine vendors via a 60+ alias normalisation engine
- **Stores** data in a versioned, SHA-256 secured PostgreSQL database (with MongoDB and SQLite alternatives)
- **Validates** data against FAIR principles and domain-specific quality rules
- **Benchmarks** 7 compression strategies against a 5% ML-accuracy degradation threshold
- **Trains** and evaluates Random Forest and Linear Regression models on NIST AM Bench data
- **Exposes** everything through a REST API and three browser-based dashboards — no coding required

The system was validated against **10 formal Acceptance Test Procedures (ATPs)** with quantitative pass/fail criteria. **9 of 10 ATPs pass** at mid-term submission.

---

## Research Questions

| # | Question | Files |
|---|---|---|
| **RQ1** | How can an AI-ready pipeline be designed to minimise storage while maintaining full ML usability? | `am_data_pipeline_postgres.py`, `load_local_dataset.py` |
| **RQ2** | What is the quantitative impact of lossless, lossy, and PCA compression on ML performance? | `ml_pipeline.py`, `data_analysis_pipeline.py` |
| **RQ3** | How can FAIR principles be operationalised and validated in an industrial AM context? | `data_quality_pipeline.py`, `version_control.py` |
| **RQ4** | What interfaces best enable non-specialist AM engineers to manage AI-ready data? | `am_dashboard.html`, `am_dashboard_advanced.html`, `index.html` |

---

## Key Results

| Metric | Value | Criterion | Status |
|---|---|---|---|
| Ingestion throughput | 12.3 rec/s | >= 5 rec/s | PASS |
| FAIR metadata completeness (M) | 0.92 | >= 0.90 | PASS |
| Parquet/Snappy delta accuracy | 0.3% | < 5% | PASS |
| Random Forest R2 (mean) | 0.781 | >= 0.70 | PASS |
| Max query time | 0.87 s | <= 5 s | PASS |
| Preprocessing time reduction | 70.8% | >= 30% | PASS |
| Formats supported | 6 | 6 | PASS |
| ATP overall | 9 / 10 PASS | 10/10 target | ATP-7 PARTIAL |

**Compression benchmark summary:**

| Strategy | Delta Acc | Storage | Verdict |
|---|---|---|---|
| Raw CSV | 0.0% | 100% | Baseline |
| **Parquet/Snappy** | **0.3%** | **22%** | **RECOMMENDED** |
| gzip CSV | 0.0% | 18% | PASS |
| PCA 99% | 1.1% | 18% | PASS |
| PCA 95% | 2.8% | 12% | PASS |
| Downsampling 1:5 | 4.2% | 20% | BORDERLINE |
| Downsampling 1:10 | 7.3% | 10% | FAIL |

---

## System Architecture

```
+---------------------------------------------------------------------+
|  LAYER 1 - Frontend Interfaces                                       |
|  am_dashboard.html  .  am_dashboard_advanced.html  .  index.html    |
+---------------------------------------------------------------------+
|  LAYER 2 - API Gateway                                               |
|  restful_api.py  .  /api/v1/  .  JWT + RBAC  .  Swagger UI          |
+---------------------------------------------------------------------+
|  LAYER 3 - Service Layer                                             |
|  data_quality_pipeline.py  .  ml_pipeline.py  .  version_control.py |
|  backup_recovery.py  .  security_privacy.py  .  collaboration.py    |
+---------------------------------------------------------------------+
|  LAYER 4 - Data Storage                                              |
|  PostgreSQL 15 (prod)  .  MongoDB 7.0 (alt)  .  SQLite 3 (dev)      |
+---------------------------------------------------------------------+
|  LAYER 5 - Ingestion & Pipeline                                      |
|  load_local_dataset.py  .  60+ alias mappings  .  Format detection  |
|  CSV . XLSX . JSON . TSV . Parquet . HDF5                           |
+---------------------------------------------------------------------+
         ^
         | Raw data from: EOS . Trumpf . SLM Solutions . NIST AM Bench
```

---

## Repository Structure

```
am-data-pipeline/
|
+-- README.md                        <- This file
+-- requirements.txt                 <- Base Python dependencies
+-- requirements_am.txt              <- AM pipeline (SQLite) dependencies
+-- requirements_postgres.txt        <- Full stack with ML
+-- requirements_mongodb.txt         <- MongoDB stack
+-- docker-compose.yml               <- Multi-service Docker config
|
+-- BACKEND
+-- am_data_pipeline.py              <- Core pipeline (SQLite backend)
+-- am_data_pipeline_postgres.py     <- PostgreSQL ORM models + CRUD
+-- am_data_pipeline_mongodb.py      <- MongoDB alternative backend
+-- api_server.py                    <- Unified server entry point
+-- restful_api.py                   <- Versioned REST API (/api/v1/)
+-- backend.py                       <- Minimal demo backend
|
+-- INGESTION
+-- load_local_dataset.py            <- Multi-format ingestion + 60+ alias map
+-- example_data_ingestion.py        <- NIST dataset loading script
|
+-- DATA QUALITY
+-- data_quality_pipeline.py         <- FAIR scoring, IQR outliers, validation
+-- data_quality_api.py              <- Quality REST endpoints
+-- data_quality_client.py           <- Client usage examples
|
+-- ML PIPELINE
+-- ml_pipeline.py                   <- RandomForest + LinearRegression train/eval
+-- ml_api.py                        <- ML REST endpoints
+-- data_analysis_pipeline.py        <- PCA, clustering, correlation analysis
+-- data_analysis_api.py             <- Analysis REST endpoints
+-- data_analysis_client.py          <- Client usage examples
|
+-- VERSION CONTROL
+-- version_control.py               <- SHA-256 versioning + rollback
+-- version_control_api.py           <- Version REST endpoints
+-- version_control_client.py        <- Client usage examples
+-- version_control_migration.py     <- DB migration helper
|
+-- OPERATIONS
+-- backup_recovery.py               <- pg_dump + checksum-verified restore
+-- security_privacy.py              <- JWT, RBAC, Fernet encryption, audit log
+-- collaboration_sharing.py         <- Share tokens, comments, invites
+-- database_migrations.py           <- Schema creation and migration
+-- visualization_generator.py       <- Matplotlib figure generation
|
+-- FRONTEND
+-- am_dashboard.html                <- Basic dashboard (CRUD + browsing)
+-- am_dashboard_advanced.html       <- Advanced visualisation (6-panel)
+-- index.html                       <- Drag-and-drop upload dashboard
|
+-- DOCUMENTATION
+-- AM-Data-Pipeline-Architecture.md
+-- README_AM_PIPELINE.md
+-- README_DATA_QUALITY.md
+-- README_DATA_ANALYSIS.md
+-- README_ML_PIPELINE.md
+-- README_REST_API.md
+-- README_VERSION_CONTROL.md
+-- README_DATABASE.md
+-- README_BACKUP_RECOVERY.md
+-- README_COLLABORATION.md
+-- README_VISUALIZATION.md
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 15 (for production) or SQLite (for development — zero config)
- Git

### Option A — Quick Start with SQLite (Recommended for evaluation)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/am-data-pipeline.git
cd am-data-pipeline

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements_am.txt

# 4. Start the server
python am_data_pipeline.py

# 5. Open the dashboard
# Navigate to: http://localhost:8000
```

### Option B — Full Stack with PostgreSQL

```bash
# 1. Install dependencies
pip install -r requirements_postgres.txt

# 2. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/am_pipeline"
export SECRET_KEY="your-secret-key-here"

# 3. Initialise the database schema
python database_migrations.py

# 4. Start the server
python api_server.py

# 5. Load example NIST data
python example_data_ingestion.py
```

### Option C — Docker (All services in one command)

```bash
docker-compose up -d
# Dashboard: http://localhost:8000
# API docs:  http://localhost:8000/docs
```

---

## Quick Start

### 1. Ingest your first experiment

```python
import requests

experiment = {
    "experiment_id": "EXP-2025-001",
    "experiment_name": "IN718 LPBF Baseline",
    "material_type": "IN718",
    "material_batch": "NIST-AMB2022-B6",
    "build_platform": "EOS M290",
    "operator": "Yalavarthi",
    "process_parameters": {
        "layer_height": 0.04,
        "print_speed": 900.0,
        "nozzle_temperature": 200.0,
        "infill_percentage": 100.0
    },
    "quality_metrics": {
        "tensile_strength_mpa": 1012.5,
        "surface_roughness_um": 9.8,
        "porosity_percent": 0.12
    }
}

r = requests.post("http://localhost:8000/api/v1/experiments", json=experiment)
print(r.json())
```

### 2. Upload a CSV with non-standard column names

The ingestion engine automatically maps vendor-specific names to the canonical schema:

```csv
scanVelocity_mmps, LaserPwr, ts_mpa, surfRough_um
900, 195, 1008.3, 9.5
```

These map to: `print_speed`, `nozzle_temperature`, `tensile_strength_mpa`, `surface_roughness_um`

```bash
# Upload via web interface
open http://localhost:8000/upload

# Or via API
curl -X POST http://localhost:8000/api/upload/csv \
     -F "file=@my_experiment_data.csv"
```

### 3. Export ML-ready dataset

```python
import requests, pandas as pd, io

# Export as Parquet (recommended — 0.3% accuracy impact, 78% storage saving)
r = requests.get("http://localhost:8000/api/v1/export/parquet")
df = pd.read_parquet(io.BytesIO(r.content))

print(df.shape)    # (100, 12)
print(df.dtypes)   # All numeric — ready for scikit-learn
```

---

## API Reference

Full OpenAPI spec at `http://localhost:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/info` | API info and version |
| `POST` | `/api/v1/experiments` | Create experiment record |
| `GET` | `/api/v1/experiments` | List and filter experiments |
| `GET` | `/api/v1/experiments/{id}` | Get single experiment |
| `PUT` | `/api/v1/experiments/{id}` | Update experiment |
| `GET` | `/api/v1/experiments/{id}/versions` | Version history |
| `POST` | `/api/v1/experiments/{id}/rollback/{v}` | Rollback to version |
| `POST` | `/api/upload/csv` | Upload CSV file |
| `GET` | `/api/v1/export/csv` | Export all data as CSV |
| `GET` | `/api/v1/export/parquet` | Export as Parquet |
| `GET` | `/api/v1/ml/train` | Trigger model training |
| `POST` | `/api/v1/ml/predict` | Run inference |
| `GET` | `/api/v1/quality/report` | FAIR quality report |
| `GET` | `/api/v1/analytics/summary` | Dataset summary statistics |
| `GET` | `/dashboard/basic` | Basic dashboard UI |
| `GET` | `/dashboard/advanced` | Advanced visualisation UI |
| `GET` | `/upload` | Upload dashboard UI |

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v1/auth/token \
     -d '{"username": "admin", "password": "your-password"}'

# Use token
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/experiments
```

Three RBAC roles: **Admin**, **Researcher**, **Viewer**

---

## Frontend Interfaces

Three browser-based dashboards — no programming knowledge required.

| Interface | File | Access URL | Purpose |
|---|---|---|---|
| Basic Dashboard | `am_dashboard.html` | `/dashboard/basic` | Experiment CRUD, browsing, CSV export |
| Advanced Viz | `am_dashboard_advanced.html` | `/dashboard/advanced` | 6-panel analytics: scatter, heatmap, ML comparison, compression chart |
| Upload Dashboard | `index.html` | `/upload` | Drag-and-drop CSV/XLSX with live alias mapping preview |

---

## ML Pipeline Usage

```python
from ml_pipeline import AMMLPipeline

pipeline = AMMLPipeline(db_url="postgresql://user:pass@localhost/am_pipeline")

# Train Random Forest
results = pipeline.train(
    material_type="IN718",      # None = all materials
    model_type="random_forest",
    test_size=0.2,
    random_state=42             # All thesis results use seed=42
)

print(f"R2:  {results['r2']:.3f}")
print(f"MAE: {results['mae']:.1f} MPa")

# Predict
prediction = pipeline.predict({
    "nozzle_temperature": 200.0,
    "print_speed": 900.0,
    "layer_height": 0.04,
    "infill_percentage": 100.0,
    "material_type": "IN718"
})
print(f"Predicted tensile strength: {prediction:.1f} MPa")
```

### Reproduce thesis benchmark results

```bash
python example_data_ingestion.py                                    # Load 100-experiment dataset
python ml_pipeline.py --benchmark --all-materials --output results.json
```

Expected output (matches Table 5.1 in thesis):
```
Material           RF R2    LR R2    RF MAE
Polycarbonate      0.812    0.734     2.41 MPa
Polyamide 12       0.798    0.712     1.86 MPa
IN625 LPBF         0.771    0.693    15.80 MPa
IN718 LPBF         0.756    0.681    18.30 MPa
Ti-6Al-4V LPBF     0.734    0.659    22.10 MPa
```

---

## Compression Benchmarking

```python
from data_analysis_pipeline import CompressionBenchmark

bench = CompressionBenchmark(threshold_pct=5.0)   # configurable
results = bench.run_all_strategies(
    data_path="nist_benchmark_dataset.csv",
    target_col="tensile_strength_mpa"
)

for strategy, metrics in results.items():
    print(f"{strategy:20s}  dAcc={metrics['delta_acc']:.1f}%  "
          f"Storage={metrics['storage_pct']:.0f}%  "
          f"Verdict={metrics['verdict']}")
```

---

## Data Quality & FAIR Compliance

```python
from data_quality_pipeline import DataQualityPipeline

pipeline = DataQualityPipeline()
report = pipeline.generate_report(material_type="IN718")

print(f"FAIR completeness M = {report['completeness_score']:.2f}")
print(f"Outliers detected:  {report['outlier_count']}")
print(f"Missing values:     {report['missing_count']}")
```

| FAIR Dimension | What is measured | Target |
|---|---|---|
| **Findable** | Unique IDs, indexed metadata | >= 0.90 |
| **Accessible** | REST API, authentication | >= 0.90 |
| **Interoperable** | Schema compliance, alias mapping | >= 0.85 |
| **Reusable** | Version history, provenance | >= 0.90 |

---

## Version Control

```python
from version_control import VersionControlSystem

vc = VersionControlSystem()

# List all versions
versions = vc.list_versions("EXP-2025-001")
for v in versions:
    print(f"v{v.version_number}  {v.created_at}  hash={v.version_hash[:8]}...")

# Roll back
vc.rollback("EXP-2025-001", version_number=2, restored_by="admin@gkn.com")

# Compare versions
diff = vc.compare("EXP-2025-001", version1=1, version2=3)
print(diff["modified_fields"])
```

Every write creates a deterministic SHA-256 hash of the full experiment record. If any field changes, the hash changes — providing tamper-evident audit trails aligned with AS9100 requirements.

---

## Docker Deployment

```bash
docker-compose up -d       # Start all services
docker-compose ps          # Check status
docker-compose logs -f api # View API logs
docker-compose down        # Stop all services
docker-compose down -v     # Stop and remove volumes (full reset)
```

| Service | Port |
|---|---|
| FastAPI server + dashboards | 8000 |
| PostgreSQL | 5432 |
| Swagger UI | 8000/docs |

---

## Running the Tests (ATPs)

```bash
# Individual ATPs
python -m pytest tests/test_atp1_ingestion.py -v   # >= 5 rec/s
python -m pytest tests/test_atp3_compression.py -v # deltaAcc < 5%
python -m pytest tests/test_atp4_ml.py -v          # RF R2 >= 0.70
python -m pytest tests/test_atp6_query.py -v       # <= 5 seconds

# All ATPs
python -m pytest tests/ -v --tb=short
```

Results expected: 9 PASS, 1 PARTIAL (ATP-7 awaiting GKN production data)

---

## Dataset & Reproducibility

- **Source:** [NIST AM Bench 2022](https://www.nist.gov/ambench/amb2022-01-description)
- **Permanent DOI:** https://data.nist.gov/od/id/mds2-2581
- All ML runs use `random_state=42`
- Regenerate benchmark: `python example_data_ingestion.py --source nist --n 100 --seed 42`

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| API Framework | FastAPI + Uvicorn | 0.104 |
| ORM | SQLAlchemy | 2.0 |
| Primary DB | PostgreSQL | 15 |
| Alternative DB | MongoDB | 7.0 |
| Dev DB | SQLite | 3 |
| ML | scikit-learn | 1.5 |
| Data | pandas + NumPy | 2.2 |
| Frontend charts | Chart.js + Plotly.js | 4.4 + 2.26 |
| Auth | JWT (PyJWT) + Fernet | — |
| Deployment | Docker + Docker Compose | — |

---

## Citation

```bibtex
@mastersthesis{yalavarthi2026am,
  author = {Srinivasa Rao Yalavarthi and Akshayakumar Srinivasan},
  title  = {Data Management Flow and Standards to Enable {AI}},
  school = {University West},
  year   = {2026},
  type   = {{MSc} Thesis, {AI} and Automation Programme}
}
```

---

## Acknowledgements

- **GKN Aerospace, Trollhättan** — industrial context and process knowledge
- **University West** — AI and Automation Programme
- **NIST** — AM Bench 2022 public benchmark datasets
- **Supervisors:** Prof. Amit Kumar Mishra
- **Examiner:** Dr. Yongcui Mi

---

## Future Work

- [ ] ATP-7: Validate at GKN production scale (1–10 GB)
- [ ] HDF5 thermographic sensor stream ingestion
- [ ] Transfer learning across material classes
- [ ] MLOps Level 3: Online model drift monitoring
- [ ] Digital thread integration with CAD/CAM data

---

## License

MIT License — see [LICENSE](LICENSE) for details.

The software will be transferred to GKN Aerospace upon project completion.

---

*Degree Project — Master of Science in AI and Automation — University West, Sweden, 2026*
