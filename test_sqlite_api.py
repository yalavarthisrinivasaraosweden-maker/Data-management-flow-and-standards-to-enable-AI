"""
Test script for am_data_pipeline.py (SQLite version)
Uses the correct unversioned endpoints: /api/experiments, /api/analytics/summary
"""

import requests
import json

API_BASE = "http://localhost:8000"

def check(label, response):
    status = "PASS" if response.ok else "FAIL"
    print(f"[{status}] {label} — HTTP {response.status_code}")
    if response.ok:
        data = response.json()
        print(json.dumps(data, indent=2, default=str)[:400])  # print first 400 chars
    else:
        print(f"       Error: {response.text[:200]}")
    print()

print("=" * 55)
print("Testing AM Data Pipeline (SQLite) API")
print("=" * 55)
print()

# 1. Analytics summary (acts as health check)
r = requests.get(f"{API_BASE}/api/analytics/summary")
check("Analytics summary", r)

# 2. List all experiments
r = requests.get(f"{API_BASE}/api/experiments")
check("List experiments", r)

# 3. Get single experiment
r = requests.get(f"{API_BASE}/api/experiments/EXP-2024-001")
check("Get experiment EXP-2024-001", r)

# 4. Get ML features
r = requests.get(f"{API_BASE}/api/experiments/EXP-2024-001/ml-features")
check("ML features for EXP-2024-001", r)

# 5. Filter by material type
r = requests.get(f"{API_BASE}/api/experiments?material_type=PLA")
check("Filter experiments by PLA", r)

# 6. Export as JSON
r = requests.get(f"{API_BASE}/api/export/ml-dataset?format=json")
check("Export ML dataset as JSON", r)

# 7. Create a new experiment
new_exp = {
    "experiment_id": "EXP-TEST-001",
    "experiment_name": "VS Code Test Experiment",
    "material_type": "PLA",
    "status": "completed",
    "process_parameters": {
        "layer_height": 0.2,
        "print_speed": 60.0,
        "nozzle_temperature": 215.0,
        "bed_temperature": 60.0,
        "infill_percentage": 25.0
    },
    "quality_metrics": {
        "tensile_strength_mpa": 44.0,
        "surface_roughness_um": 9.0,
        "porosity_percent": 2.5
    }
}
r = requests.post(
    f"{API_BASE}/api/experiments",
    json=new_exp,
    headers={"Content-Type": "application/json"}
)
check("Create new experiment", r)

print("=" * 55)
print("All tests complete.")
print(f"Open http://localhost:8000 to see the dashboard.")
print(f"Open http://localhost:8000/docs to see all API endpoints.")
print("=" * 55)