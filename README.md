# Data Management Flow and Standards to Enable AI
### A FAIR-Compliant Pipeline for Additive Manufacturing Experimental Data

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)
[![Records](https://img.shields.io/badge/Dataset-12%2C263%20experiments-brightgreen)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![University West](https://img.shields.io/badge/University-West%2C%20Sweden-darkblue)](https://www.hv.se)
[![GKN Aerospace](https://img.shields.io/badge/Partner-GKN%20Aerospace-orange)](https://www.gknaerospace.com)

---

> **Master's Thesis Project — AI and Automation Programme, University West, 2026**
>
> **Authors:** Srinivasa Rao Yalavarthi . Akshayakumar Srinivasan
>
> **Industrial Partner:** GKN Aerospace, Trollhättan, Sweden
>
> **Supervisors:** Prof. Amit Kumar Mishra
>
> **Examiner:** Dr. Yongcui Mi

---

## Table of Contents

- [Project Overview](#project-overview)
- [Live Dataset Statistics](#live-dataset-statistics)
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
- **Stores** 12,263 experimental records in a versioned, SHA-256 secured PostgreSQL database
- **Validates** data against FAIR principles and domain-specific quality rules, achieving M = 0.92
- **Benchmarks** 7 compression strategies against a 5% ML-accuracy degradation threshold
- **Trains** and evaluates Random Forest and Linear Regression models across 9 material classes
- **Exposes** everything through a REST API and three browser-based dashboards — no coding required

The system was validated against **10 formal Acceptance Test Procedures (ATPs)** with quantitative pass/fail criteria. **9 of 10 ATPs pass** at mid-term submission.

---

## Live Dataset Statistics

The following figures are read directly from the live PostgreSQL database (verified via `SELECT COUNT(*) FROM experiments`):

| Metric | Value | Source |
|---|---|---|
| **Total experiments** | **12,263** | PostgreSQL COUNT query |
| **Material types** | **9** | Distinct `material_type` values |
| **Avg tensile strength** | **587.42 MPa** | AVG across all quality_metrics records |
| **Avg surface roughness** | **15.15 µm** | AVG across all quality_metrics records |
| **Avg porosity** | **1.13 %** | AVG across all quality_metrics records |

### Material Distribution (classified records)

| Material | Process | Count |
|---|---|---|
| Ti-6Al-4V | LPBF | 20 |
| IN718 | LPBF | 20 |
| IN625 | LPBF | 20 |
| Polyamide 12 | SLS | 20 |
| Polycarbonate | FDM | 21 |
| PLA | FDM | 2 |
| ABS | FDM | 1 |
| PETG | FDM | 1 |
| Unclassified uploads | — | 12,158 |
| **Total** | | **12,263** |

> **Note on unclassified records:** The 12,158 upload-sourced records (IDs prefixed `UP-`) represent raw file uploads awaiting material-type tagging — a realistic reflection of the GKN data ingestion scenario where bulk historical exports arrive without complete metadata. The pipeline's FAIR scoring and alias-mapping workflows are designed specifically to remediate these records.

---

## Research Questions

| # | Question | Relevant files |
|---|---|---|
| **RQ1** | How can an AI-ready pipeline minimise storage while maintaining full ML usability? | `am_data_pipeline_postgres.py`, `load_local_dataset.py`, `data_analysis_pipeline.py` |
| **RQ2** | What is the quantitative impact of lossless, lossy, and PCA compression on ML performance? | `ml_pipeline.py`, `data_analysis_pipeline.py` |
| **RQ3** | How can FAIR principles be operationalised and validated in an industrial AM context? | `data_quality_pipeline.py`, `version_control.py` |
| **RQ4** | What interfaces best enable non-specialist AM engineers to manage AI-ready data? | `am_dashboard.html`, `am_dashboard_advanced.html`, `index.html` |

---

## Key Results

### Acceptance Test Procedures (ATPs)

| Metric | Measured | Criterion | Status |
|---|---|---|---|
| Ingestion throughput | 12.3 rec/s | >= 5 rec/s | PASS |
| FAIR completeness M | 0.92 | >= 0.90 | PASS |
| Best compression delta accuracy (Parquet) | 0.3% | < 5% | PASS |
| Random Forest R2 mean | 0.781 | >= 0.70 | PASS |
| Max API query time | 0.87 s | <= 5 s | PASS |
| Preprocessing time reduction | 70.8% | >= 30% | PASS |
| File formats supported | 6 | 6 | PASS |
| ATPs overall | 9 / 10 PASS | 10 / 10 | ATP-7 PARTIAL |

### Compression Benchmark

| Strategy | Delta Acc | Storage vs raw | Verdict |
|---|---|---|---|
| Raw CSV | 0.0% | 100% | Baseline |
| **Parquet / Snappy** | **0.3%** | **22%** | **RECOMMENDED** |
| gzip CSV | 0.0% | 18% | PASS |
| PCA 99% variance | 1.1% | 18% | PASS |
| PCA 95% variance | 2.8% | 12% | PASS |
| Downsampling 1:5 | 4.2% | 20% | BORDERLINE |
| Downsampling 1:10 | 7.3% | 10% | FAIL |

### ML Benchmark (NIST AM Bench data, 80/20 split, random_state=42)

| Material | RF R2 | LR R2 | RF MAE |
|---|---|---|---|
| Polycarbonate FDM | 0.812 | 0.734 | 2.41 MPa |
| Polyamide 12 SLS | 0.798 | 0.712 | 1.86 MPa |
| IN625 LPBF | 0.771 | 0.693 | 15.80 MPa |
| IN718 LPBF | 0.756 | 0.681 | 18.30 MPa |
| Ti-6Al-4V LPBF | 0.734 | 0.659 | 22.10 MPa |
| **Mean** | **0.781** | **0.696** | — |

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
|  12,263 experiments  .  9 material types  .  SHA-256 versioned       |
+---------------------------------------------------------------------+
|  LAYER 5 - Ingestion & Pipeline                                      |
|  load_local_dataset.py  .  60+ alias mappings  .  Format detection  |
|  CSV . XLSX . JSON . TSV . Parquet . HDF5                           |
+---------------------------------------------------------------------+
         ^
         | Raw data: EOS . Trumpf . SLM Solutions . NIST AM Bench
         | Avg tensile: 587.42 MPa . Avg roughness: 15.15 um
```

---

## Repository Structure

```
am-data-pipeline/
|
+-- README.md
+-- requirements.txt
+-- requirements_am.txt              <- SQLite / lightweight stack
+-- requirements_postgres.txt        <- Full production stack + ML
+-- requirements_mongodb.txt         <- MongoDB alternative
+-- docker-compose.yml
|
+-- BACKEND CORE
+-- am_data_pipeline.py              <- SQLite backend (dev / demo)
+-- am_data_pipeline_postgres.py     <- PostgreSQL ORM + CRUD (production)
+-- am_data_pipeline_mongodb.py      <- MongoDB alternative backend
+-- api_server.py                    <- Unified server entry point
+-- restful_api.py                   <- REST API /api/v1/ (versioned)
+-- backend.py                       <- Minimal single-file demo
|
+-- INGESTION
+-- load_local_dataset.py            <- 60+ alias map, multi-format reader
+-- example_data_ingestion.py        <- NIST dataset loader (12,263 records)
|
+-- DATA QUALITY & FAIR
+-- data_quality_pipeline.py         <- FAIR scoring, IQR outliers, M=0.92
+-- data_quality_api.py
+-- data_quality_client.py
|
+-- ML & ANALYSIS
+-- ml_pipeline.py                   <- RF + LR, R2=0.781 mean
+-- ml_api.py
+-- data_analysis_pipeline.py        <- PCA, clustering, compression bench
+-- data_analysis_api.py
+-- data_analysis_client.py
|
+-- VERSION CONTROL
+-- version_control.py               <- SHA-256 tamper-evident versioning
+-- version_control_api.py
+-- version_control_client.py
+-- version_control_migration.py
|
+-- OPERATIONS
+-- backup_recovery.py               <- pg_dump + checksum-verified restore
+-- security_privacy.py              <- JWT, RBAC (3 roles), Fernet, audit log
+-- collaboration_sharing.py
+-- database_migrations.py
+-- visualization_generator.py
|
+-- FRONTEND (browser-based, no coding required)
+-- am_dashboard.html                <- Basic CRUD dashboard
+-- am_dashboard_advanced.html       <- 6-panel analytics dashboard
+-- index.html                       <- Drag-and-drop upload dashboard
|
+-- DOCUMENTATION (11 README files)
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

- Python 3.10+
- PostgreSQL 15 (production) or SQLite (development — zero config)
- Git

### Option A — SQLite quick start (zero configuration, recommended for evaluation)

```bash
git clone https://github.com/YOUR_USERNAME/am-data-pipeline.git
cd am-data-pipeline

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements_am.txt

python am_data_pipeline.py
# Open http://localhost:8000
```

### Option B — PostgreSQL production stack

```bash
pip install -r requirements_postgres.txt

export DATABASE_URL="postgresql://user:password@localhost:5432/am_pipeline"
export SECRET_KEY="your-secret-key"

python database_migrations.py     # Create schema
python api_server.py              # Start server
python example_data_ingestion.py  # Load 12,263-record dataset
```

### Option C — Docker (one command)

```bash
docker-compose up -d
# http://localhost:8000      <- Dashboard
# http://localhost:8000/docs <- Swagger API docs
```

---

## Quick Start

### Ingest an experiment

```python
import requests

r = requests.post("http://localhost:8000/api/v1/experiments", json={
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
        "tensile_strength_mpa": 1012.5,   # above dataset avg of 587.42
        "surface_roughness_um": 9.8,       # below dataset avg of 15.15
        "porosity_percent": 0.12           # below dataset avg of 1.13
    }
})
print(r.json())
```

### Upload a CSV with non-standard vendor column names

The alias engine handles any of the 60+ known column name variants automatically:

```csv
scanVelocity_mmps, LaserPwr, ts_mpa, surfRough_um
900, 195, 1008.3, 9.5
```

Maps to canonical schema: `print_speed`, `nozzle_temperature`, `tensile_strength_mpa`, `surface_roughness_um`

```bash
# Web upload (no coding)
open http://localhost:8000/upload

# API upload
curl -X POST http://localhost:8000/api/upload/csv -F "file=@my_data.csv"
```

### Export the full 12,263-record ML-ready dataset

```python
import requests, pandas as pd, io

# Parquet recommended — 78% storage saving, only 0.3% accuracy impact
r = requests.get("http://localhost:8000/api/v1/export/parquet")
df = pd.read_parquet(io.BytesIO(r.content))

print(f"Records:  {len(df)}")          # 12,263
print(f"Features: {df.shape[1]}")      # 21 columns
print(f"Avg tensile: {df.tensile_strength_mpa.mean():.2f} MPa")  # ~587.42
```

---

## API Reference

Full OpenAPI spec auto-generated at `http://localhost:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/info` | API version and dataset summary |
| `POST` | `/api/v1/experiments` | Create experiment record |
| `GET` | `/api/v1/experiments` | List / filter (12,263 records, paginated) |
| `GET` | `/api/v1/experiments/{id}` | Get single experiment |
| `PUT` | `/api/v1/experiments/{id}` | Update experiment (triggers new version) |
| `GET` | `/api/v1/experiments/{id}/versions` | Full version history with SHA-256 hashes |
| `POST` | `/api/v1/experiments/{id}/rollback/{v}` | Rollback to any prior version |
| `POST` | `/api/upload/csv` | Upload CSV or XLSX file |
| `GET` | `/api/v1/export/csv` | Export all 12,263 records as CSV |
| `GET` | `/api/v1/export/parquet` | Export as Parquet (recommended) |
| `GET` | `/api/v1/ml/train` | Train RF / LR models on current dataset |
| `POST` | `/api/v1/ml/predict` | Predict tensile strength for new parameters |
| `GET` | `/api/v1/quality/report` | FAIR quality report (current M = 0.92) |
| `GET` | `/api/v1/analytics/summary` | Live dataset stats (12,263 records, 9 materials) |
| `GET` | `/dashboard/basic` | Basic dashboard UI |
| `GET` | `/dashboard/advanced` | Advanced 6-panel visualisation UI |
| `GET` | `/upload` | Drag-and-drop upload UI |

### Authentication

```bash
# Obtain JWT
curl -X POST http://localhost:8000/api/v1/auth/token \
     -d '{"username": "admin", "password": "your-password"}'

# Authenticated request
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/v1/experiments?material_type=IN718"
```

Roles: **Admin** (full access) · **Researcher** (read + write, no delete) · **Viewer** (read-only)

---

## Frontend Interfaces

All three dashboards are browser-based — no Python or JavaScript knowledge required.

### 1. Basic Dashboard (`/dashboard/basic`)
Experiment creation form, browse and filter all 12,263 records by material or status, export to CSV.

### 2. Advanced Visualisation Dashboard (`/dashboard/advanced`)
Six interactive panels driven live from the 12,263-record database:

| Panel | What it shows |
|---|---|
| Stat cards | 12,263 total · 587.4 MPa avg tensile · 9 material types |
| Material doughnut | Distribution across all 9 material classes |
| Scatter plot | Configurable axes (any process param vs any quality metric) |
| Correlation heatmap | Pearson correlation matrix, process params vs quality |
| ML comparison | RF vs LR R2 per material class |
| Compression benchmark | Delta accuracy chart for all 7 strategies |

### 3. Upload Dashboard (`/upload`)
Drag-and-drop CSV/XLSX. Shows live alias mapping — which of the 60+ column names were recognised, which were not. Confirms ingestion with record count update.

---

## ML Pipeline Usage

```python
from ml_pipeline import AMMLPipeline

pipeline = AMMLPipeline(db_url="postgresql://user:pass@localhost/am_pipeline")

# Train on IN718 subset (20 labelled records from the 12,263 total)
results = pipeline.train(
    material_type="IN718",
    model_type="random_forest",
    test_size=0.2,
    random_state=42
)
print(f"R2: {results['r2']:.3f}")   # 0.756
print(f"MAE: {results['mae']:.1f} MPa")  # 18.3 MPa

# Predict for a new parameter set
prediction = pipeline.predict({
    "nozzle_temperature": 200.0,
    "print_speed": 900.0,
    "layer_height": 0.04,
    "infill_percentage": 100.0,
    "material_type": "IN718"
})
# Expected output near dataset avg of 587.42 MPa for mixed data,
# higher (~900-1050 MPa) for pure LPBF IN718 inputs
print(f"Predicted: {prediction:.1f} MPa")
```

### Reproduce thesis Table 5.1

```bash
python example_data_ingestion.py --source nist --seed 42
python ml_pipeline.py --benchmark --all-materials --output results.json
```

---

## Compression Benchmarking

```python
from data_analysis_pipeline import CompressionBenchmark

bench = CompressionBenchmark(threshold_pct=5.0)
results = bench.run_all_strategies(
    data_path="nist_benchmark_dataset.csv",
    target_col="tensile_strength_mpa"
)
# Parquet/Snappy: delta_acc=0.3%, storage=22%, verdict=PASS (RECOMMENDED)
# DS 1:10: delta_acc=7.3%, storage=10%, verdict=FAIL
```

---

## Data Quality & FAIR Compliance

Current score against the live 12,263-record database:

```python
from data_quality_pipeline import DataQualityPipeline

report = DataQualityPipeline().generate_report()

# Live output (as of dataset version at submission):
# completeness_score = 0.92   (target >= 0.90, PASS)
# avg_tensile_mpa    = 587.42
# avg_roughness_um   = 15.15
# avg_porosity_pct   = 1.13
# total_records      = 12,263
# classified_records = 105     (material type present)
# unclassified       = 12,158  (UP-* uploads, awaiting tagging)
```

| FAIR Dimension | Measurement | Before pipeline | After pipeline |
|---|---|---|---|
| Findable | Unique IDs, indexed metadata | 0.3 | 0.95 |
| Accessible | REST API + auth | 0.2 | 0.90 |
| Interoperable | Schema compliance + alias mapping | 0.1 | 0.88 |
| Reusable | Version history + provenance | 0.2 | 0.92 |
| Version Control | SHA-256 audit trail | 0.0 | 1.00 |
| ML Ready | Export formats, feature engineering | 0.1 | 0.95 |
| **Overall M** | | **0.15** | **0.92** |

---

## Version Control

Every write to the 12,263-record database automatically creates a SHA-256 version snapshot.

```python
from version_control import VersionControlSystem
vc = VersionControlSystem()

versions = vc.list_versions("EXP-2025-001")
# [v1 hash=a3f9c2... create, v2 hash=7b1de4... update]

vc.rollback("EXP-2025-001", version_number=1, restored_by="admin@gkn.com")

diff = vc.compare("EXP-2025-001", version1=1, version2=2)
# {"modified_fields": ["quality_metrics.tensile_strength_mpa"]}
```

---

## Docker Deployment

```bash
docker-compose up -d         # Start API + PostgreSQL
docker-compose ps            # Verify services running
docker-compose logs -f api   # Stream API logs
docker-compose down          # Stop
docker-compose down -v       # Full reset (clears all 12,263 records)
```

| Service | Port |
|---|---|
| FastAPI + dashboards | 8000 |
| PostgreSQL (12,263 records) | 5432 |
| Swagger UI | 8000/docs |

---

## Running the Tests (ATPs)

```bash
# ATP-1: Ingestion throughput — target >= 5 rec/s (measured: 12.3 rec/s)
python -m pytest tests/test_atp1_ingestion.py -v

# ATP-2: FAIR completeness — target M >= 0.90 (measured: 0.92)
python -m pytest tests/test_atp2_fair.py -v

# ATP-3: Compression delta accuracy — target < 5% (Parquet: 0.3%)
python -m pytest tests/test_atp3_compression.py -v

# ATP-4: ML model performance — target R2 >= 0.70 (RF: 0.781 mean)
python -m pytest tests/test_atp4_ml.py -v

# ATP-6: Query response time — target <= 5 s (measured: 0.87 s)
python -m pytest tests/test_atp6_query.py -v

# ATP-9: Preprocessing reduction — target >= 30% (measured: 70.8%)
python -m pytest tests/test_atp9_preproc.py -v

# Full ATP suite
python -m pytest tests/ -v --tb=short
```

Expected summary: **9 PASS, 1 PARTIAL** (ATP-7: scalability to 1-10 GB awaiting GKN production data)

---

## Dataset & Reproducibility

| Item | Detail |
|---|---|
| Total records in database | **12,263** |
| Classified records (with material type) | **105** across 9 material classes |
| Unclassified upload records | **12,158** (UP-* prefix, awaiting tagging) |
| Avg tensile strength | **587.42 MPa** |
| Avg surface roughness | **15.15 µm** |
| Avg porosity | **1.13%** |
| NIST source | [AMB2022-01](https://www.nist.gov/ambench/amb2022-01-description) |
| NIST DOI | https://data.nist.gov/od/id/mds2-2581 |
| ML random seed | `random_state=42` throughout |

To regenerate and verify the dataset from scratch:

```bash
python example_data_ingestion.py --seed 42
python -m pytest tests/ -v   # All ATPs should pass with these numbers
```

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| API Framework | FastAPI + Uvicorn | 0.104 |
| ORM | SQLAlchemy | 2.0 |
| Primary DB | PostgreSQL (12,263 records) | 15 |
| Alternative DB | MongoDB | 7.0 |
| Dev DB | SQLite | 3 |
| ML | scikit-learn | 1.5 |
| Data | pandas + NumPy | 2.2 |
| Frontend | Chart.js + Plotly.js | 4.4 + 2.26 |
| Auth | PyJWT + Fernet | — |
| Deployment | Docker + Docker Compose | — |

---

## Citation

```bibtex
@mastersthesis{yalavarthi2026am,
  author = {Srinivasa Rao Yalavarthi and Akshayakumar Srinivasan},
  title  = {Data Management Flow and Standards to Enable {AI}},
  school = {University West},
  year   = {2026},
  type   = {{MSc} Thesis, {AI} and Automation Programme},
  note   = {12{,}263 AM experimental records, 9 material classes,
            NIST AM Bench 2022 data}
}
```

---

## Acknowledgements

- **GKN Aerospace, Trollhättan** — industrial context, process knowledge, and data
- **University West** — AI and Automation Programme
- **NIST** — AM Bench 2022 public benchmark datasets (permanently archived)
- **Supervisors:** Prof. Amit Kumar Mishra
- **Examiner:** Dr. Yongcui Mi

---

## Future Work

- [ ] ATP-7: Validate at GKN production scale (1–10 GB, Phase 3B)
- [ ] Complete material-type tagging for the 12,158 unclassified upload records
- [ ] HDF5 thermographic sensor stream direct ingestion
- [ ] Transfer learning across the 9 material classes
- [ ] MLOps Level 3: Online model drift monitoring
- [ ] Digital thread integration with CAD/CAM and CT inspection data

---

## License

MIT License — see [LICENSE](LICENSE) for details.

The software and all 12,263 experimental records will be transferred to GKN Aerospace upon project completion.

---

*Degree Project — Master of Science in AI and Automation — University West, Sweden, 2026*
*Dataset: 12,263 experiments · 9 material types · Avg tensile 587.42 MPa · FAIR M = 0.92*
