"""
Example script for ingesting AM experimental data into the pipeline
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

# Example experiment data
example_experiments = [
    {
        "experiment_id": "EXP-2024-001",
        "experiment_name": "PLA High Speed Test",
        "material_type": "PLA",
        "material_batch": "BATCH-2024-01",
        "build_platform": "Ender 3 Pro",
        "build_date": "2024-01-15T10:00:00",
        "operator": "John Doe",
        "status": "completed",
        "notes": "Initial high-speed printing test",
        "process_parameters": {
            "layer_height": 0.2,
            "print_speed": 80.0,
            "nozzle_temperature": 210.0,
            "bed_temperature": 60.0,
            "infill_percentage": 20.0,
            "infill_pattern": "grid",
            "shell_count": 3,
            "support_enabled": False,
            "print_time_hours": 2.5
        },
        "geometry_data": {
            "part_name": "Test Cube",
            "volume_mm3": 1000.0,
            "surface_area_mm2": 600.0,
            "bounding_box_x": 10.0,
            "bounding_box_y": 10.0,
            "bounding_box_z": 10.0,
            "complexity_score": 1.0
        },
        "quality_metrics": {
            "tensile_strength_mpa": 45.2,
            "surface_roughness_um": 8.5,
            "porosity_percent": 2.1,
            "density_g_per_cm3": 1.24,
            "defect_count": 0,
            "measurement_method": "Standard ASTM testing"
        }
    },
    {
        "experiment_id": "EXP-2024-002",
        "experiment_name": "ABS Temperature Study",
        "material_type": "ABS",
        "material_batch": "BATCH-2024-02",
        "build_platform": "Prusa i3",
        "build_date": "2024-01-20T14:30:00",
        "operator": "Jane Smith",
        "status": "completed",
        "notes": "Temperature optimization study",
        "process_parameters": {
            "layer_height": 0.15,
            "print_speed": 50.0,
            "nozzle_temperature": 250.0,
            "bed_temperature": 90.0,
            "infill_percentage": 30.0,
            "infill_pattern": "honeycomb",
            "shell_count": 4,
            "support_enabled": True,
            "support_type": "tree",
            "print_time_hours": 4.2
        },
        "geometry_data": {
            "part_name": "Tensile Test Specimen",
            "volume_mm3": 2500.0,
            "surface_area_mm2": 1800.0,
            "bounding_box_x": 50.0,
            "bounding_box_y": 10.0,
            "bounding_box_z": 5.0,
            "complexity_score": 2.5
        },
        "quality_metrics": {
            "tensile_strength_mpa": 38.5,
            "yield_strength_mpa": 32.1,
            "elongation_percent": 12.5,
            "surface_roughness_um": 12.3,
            "porosity_percent": 3.5,
            "density_g_per_cm3": 1.05,
            "defect_count": 2,
            "defect_types": "Layer adhesion, minor warping",
            "measurement_method": "ASTM D638"
        }
    },
    {
        "experiment_id": "EXP-2024-003",
        "experiment_name": "PETG Layer Height Optimization",
        "material_type": "PETG",
        "material_batch": "BATCH-2024-03",
        "build_platform": "Ender 3 Pro",
        "build_date": "2024-02-01T09:00:00",
        "operator": "John Doe",
        "status": "completed",
        "process_parameters": {
            "layer_height": 0.1,
            "print_speed": 60.0,
            "nozzle_temperature": 235.0,
            "bed_temperature": 80.0,
            "infill_percentage": 25.0,
            "infill_pattern": "grid",
            "shell_count": 3,
            "support_enabled": False,
            "print_time_hours": 3.8
        },
        "geometry_data": {
            "part_name": "Surface Quality Test",
            "volume_mm3": 1500.0,
            "surface_area_mm2": 1200.0,
            "bounding_box_x": 15.0,
            "bounding_box_y": 15.0,
            "bounding_box_z": 10.0,
            "complexity_score": 1.8
        },
        "quality_metrics": {
            "tensile_strength_mpa": 52.3,
            "surface_roughness_um": 5.2,
            "porosity_percent": 1.8,
            "density_g_per_cm3": 1.27,
            "defect_count": 0,
            "measurement_method": "Optical profilometry"
        }
    }
]

def ingest_experiment(experiment_data):
    """Ingest a single experiment. Returns 'created', 'skipped', or 'failed'."""
    exp_id = experiment_data["experiment_id"]
    try:
        response = requests.post(
    f"{API_BASE}/api/v1/experiments",
    json=experiment_data,
    headers={"Content-Type": "application/json"},
    timeout=30,
)
        if response.status_code == 400:
            try:
                detail = response.json().get("detail", "")
            except (ValueError, TypeError):
                detail = ""
            if detail == "Experiment ID already exists":
                print(f"⊙ Skipped (already in database): {exp_id}")
                return "skipped"
        response.raise_for_status()
        print(f"✓ Successfully ingested: {exp_id}")
        return "created"
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to ingest {exp_id}: {e}")
        if e.response is not None:
            print(f"  Error details: {e.response.text}")
        return "failed"

def main():
    print("Starting AM Experimental Data Ingestion...")
    print(f"API Base URL: {API_BASE}\n")
    
    created = skipped = failed = 0
    for exp in example_experiments:
        outcome = ingest_experiment(exp)
        if outcome == "created":
            created += 1
        elif outcome == "skipped":
            skipped += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(
        f"Ingestion complete: {created} created, {skipped} skipped (already present), {failed} failed"
    )
    
    # Fetch ML features for the first experiment when data is present (new or existing)
    if failed == 0 and (created > 0 or skipped > 0):
        print("\nFetching ML features for first experiment...")
        try:
            response = requests.get(f"{API_BASE}/api/v1/experiments/EXP-2024-001/ml-features")
            features = response.json()
            print("ML Features:")
            print(json.dumps(features, indent=2))
        except Exception as e:
            print(f"Error fetching ML features: {e}")

if __name__ == "__main__":
    main()
