# AM Experimental Data Management Pipeline
## Technical Architecture & Recommended Tech Stack

---

## 1. Executive Summary

This document outlines the technical architecture for a comprehensive data management pipeline supporting Additive Manufacturing (AM) experimental data. The system is designed for efficient storage, easy access, ML/AI readiness, and enterprise-grade operations.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │  Data Viz    │  │  ML Studio   │  │  Admin UI    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY / BFF                                    │
│                    REST API · Authentication · Rate Limiting                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   DATA SERVICE        │  │   ML/AI SERVICE       │  │   COLLABORATION       │
│   (CRUD, Search)      │  │   (Training, Infer)   │  │   (Sharing, Versions) │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │  MongoDB     │  │  Object      │  │  ML Model    │         │
│  │  (Metadata)  │  │  (Documents) │  │  Storage     │  │  Registry    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PIPELINE LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Ingestion   │  │  Cleaning &  │  │  Version     │  │  Backup &    │         │
│  │  Pipeline    │  │  Preprocess  │  │  Control     │  │  Recovery    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Recommended Tech Stack

### 3.1 Backend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **API Framework** | **FastAPI** | Async support, automatic OpenAPI docs, Pydantic validation, high performance |
| **Task Queue** | **Celery** + Redis | Background jobs for ingestion, cleaning, ML training |
| **Pipeline Orchestration** | **Prefect** or **Apache Airflow** | DAG-based workflows for data pipelines; Prefect is simpler for Python-native teams |

### 3.2 Database & Storage

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Primary Metadata DB** | **PostgreSQL** | ACID compliance, rich querying, JSONB for flexible fields, strong ecosystem for analytics |
| **Document / Raw Data** | **MongoDB** (optional) or **PostgreSQL + JSONB** | Use MongoDB if you have highly nested, variable-schema experiment logs; otherwise JSONB in Postgres simplifies the stack |
| **Object Storage** | **MinIO** (self-hosted) or **AWS S3** | Raw files, large binaries, scan images, CAD models |
| **ML Model Registry** | **MLflow** | Versioning, tracking, deployment of ML models |
| **Vector DB** (if needed for AI) | **pgvector** or **Qdrant** | Semantic search, embeddings for RAG/retrieval |

**Recommendation:** Start with **PostgreSQL + MinIO/S3** to keep the stack simple. Add MongoDB only if document schema is highly variable across experiments.

### 3.3 Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | **React** + **TypeScript** | Component-based, large ecosystem, strong typing |
| **UI Library** | **Shadcn/ui** or **MUI** | Accessible, customizable, professional look |
| **Charts/Visualization** | **Plotly** (via react-plotly.js) or **Recharts** | Scientific plots, interactive dashboards |
| **State Management** | **TanStack Query** + **Zustand** | Server state + lightweight client state |
| **Build Tool** | **Vite** | Fast HMR, modern tooling |

**Alternative:** **Streamlit** or **Dash** for rapid prototyping and internal dashboards if a full React app is not required initially.

### 3.4 Security & Identity

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Authentication** | **OAuth 2.0** / **OpenID Connect** | Industry standard, SSO support |
| **Implementation** | **Keycloak** (self-hosted) or **Auth0** | Centralized identity management |
| **API Auth** | **JWT** + **OAuth2** | Stateless API authentication |

### 3.5 Infrastructure & DevOps

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Containerization** | **Docker** + **Docker Compose** | Reproducible environments |
| **Orchestration** (scale) | **Kubernetes** | Optional for production scaling |
| **CI/CD** | **GitHub Actions** or **GitLab CI** | Automated testing and deployment |
| **Secrets** | **HashiCorp Vault** or env vars | Secure credential management |
| **Monitoring** | **Prometheus** + **Grafana** | Metrics and dashboards |
| **Logging** | **Loki** or **ELK Stack** | Centralized logs |

---

## 4. Component Architecture

### 4.1 Data Ingestion Pipeline

- **Inputs:** Lab instruments, CSV/Excel exports, API feeds, manual uploads
- **Process:** Validate → Parse → Normalize → Store (metadata in Postgres, files in object storage)
- **Tools:** FastAPI endpoints for upload, Celery for async processing, Pydantic for schema validation

### 4.2 Cleaning & Preprocessing Pipeline

- **Inputs:** Raw data from ingestion
- **Process:** Deduplication, outlier detection, normalization, feature extraction
- **Outputs:** Clean datasets stored with version IDs, lineage tracked
- **Tools:** Pandas/Polars, scikit-learn preprocessing, custom transformers

### 4.3 Version Control for Data

- **Approach:** Dataset versioning (snapshots) rather than file-level Git
- **Implementation:** 
  - Metadata table: `dataset_versions` (version_id, parent_id, created_at, checksum)
  - Immutable object storage paths: `/{dataset_id}/{version_id}/...`
- **Optional:** **DVC (Data Version Control)** for ML datasets if tightly integrated with Git

### 4.4 ML/AI Pipeline

- **Training:** Track experiments with **MLflow**, store models in registry
- **Inference:** FastAPI service loading models from registry
- **Feature Store** (optional): **Feast** or custom PostgreSQL tables for consistent features across train/serve

### 4.5 Backup & Recovery

- **PostgreSQL:** pg_dump + WAL archiving, or managed backup (e.g., AWS RDS)
- **Object Storage:** Versioning enabled, cross-region replication for critical data
- **Schedule:** Daily incremental, weekly full

### 4.6 Collaboration & Sharing

- **Permissions:** Role-based access (Admin, Researcher, Viewer) at project/dataset level
- **Sharing:** Invite links, export to external formats, API keys for programmatic access
- **Audit:** Log all access and modifications for compliance

---

## 5. Data Model (Conceptual)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Project      │────▶│   Experiment    │────▶│   Dataset       │
│  - id           │     │  - id           │     │  - id           │
│  - name         │     │  - project_id   │     │  - experiment_id│
│  - owners       │     │  - metadata     │     │  - version      │
└─────────────────┘     └─────────────────┘     │  - file_refs    │
                                                └─────────────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Raw Files     │
                                                │  (Object Store) │
                                                └─────────────────┘
```

---

## 6. API Design (RESTful)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/experiments` | List experiments (filterable) |
| POST | `/api/v1/experiments` | Create experiment |
| POST | `/api/v1/experiments/{id}/upload` | Upload raw data |
| GET | `/api/v1/datasets` | List datasets |
| GET | `/api/v1/datasets/{id}/versions` | List dataset versions |
| GET | `/api/v1/datasets/{id}/download` | Download dataset |
| POST | `/api/v1/pipeline/run` | Trigger pipeline (ingest, clean, etc.) |
| GET | `/api/v1/ml/models` | List registered models |
| POST | `/api/v1/ml/predict` | Run inference |

---

## 7. Deployment Options

### Option A: Single Server (MVP)
- Docker Compose: Postgres, FastAPI, React (static), MinIO, Redis, Celery
- Suitable for lab or small team

### Option B: Cloud-Native (Scale)
- Managed Postgres (e.g., AWS RDS, Azure Database)
- S3/GCS for object storage
- ECS/EKS or App Service for backend
- CDN for frontend

### Option C: Hybrid
- On-prem Postgres + object storage for sensitive data
- Cloud for compute-intensive ML and analytics

---

## 8. Implementation Phases

| Phase | Scope | Duration (Est.) |
|-------|-------|-----------------|
| **Phase 1** | PostgreSQL + FastAPI + basic CRUD, MinIO for files, simple React dashboard | 4–6 weeks |
| **Phase 2** | Ingestion pipeline, cleaning/preprocessing, versioning | 3–4 weeks |
| **Phase 3** | Auth, RBAC, collaboration, sharing | 2–3 weeks |
| **Phase 4** | ML pipeline (MLflow), visualization enhancements | 3–4 weeks |
| **Phase 5** | Backup, monitoring, security hardening | 2–3 weeks |

---

## 9. Summary: Minimal Viable Stack

For fastest time-to-value:

- **Backend:** FastAPI + PostgreSQL + MinIO + Celery + Redis  
- **Frontend:** React + TypeScript + Shadcn/ui + Plotly  
- **Auth:** JWT (simple) or Keycloak (enterprise)  
- **ML:** MLflow  
- **Deploy:** Docker Compose  

This stack supports all stated requirements while remaining manageable for a small team and extensible for future growth.
