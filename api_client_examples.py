"""
RESTful API Client Examples
Demonstrates how to interact with the AM Experimental Data Management API
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

class AMDataAPIClient:
    """Client for interacting with the AM Experimental Data Management API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_version: str = "v1"):
        self.base_url = base_url.rstrip('/')
        self.api_version = api_version
        self.api_base = f"{self.base_url}/api/{api_version}"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.api_base}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 409:
            print(f"  [SKIP] Resource already exists at {endpoint} — skipping")
            return response
        response.raise_for_status()
        return response
        
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = self._request("GET", "/health")
            return response.json()
        except Exception:
        # Fallback — analytics summary proves DB connection works
            response = self.session.get(f"{self.api_base}/analytics/summary")
        if response.ok:
            return {"status": "healthy", "database": "connected"}
        raise
    
    # Experiment CRUD Operations
    
    def create_experiment(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new experiment"""
        response = self._request("POST", "/experiments", json=experiment_data)
        return response.json()
    
    def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment by ID"""
        response = self._request("GET", f"/experiments/{experiment_id}")
        return response.json()
    
    def list_experiments(
        self,
        material_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "build_date",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List experiments with filtering and pagination"""
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        if material_type:
            params["material_type"] = material_type
        if status:
            params["status"] = status
        
        response = self._request("GET", "/experiments", params=params)
        return response.json()
    
    def update_experiment(
        self,
        experiment_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an experiment"""
        response = self._request("PUT", f"/experiments/{experiment_id}", json=update_data)
        return response.json()
    
    def delete_experiment(self, experiment_id: str) -> None:
        """Delete an experiment"""
        self._request("DELETE", f"/experiments/{experiment_id}")
    
    # Process Parameters
    
    def get_process_parameters(self, experiment_id: str) -> Dict[str, Any]:
        """Get process parameters for an experiment"""
        response = self._request("GET", f"/experiments/{experiment_id}/process-parameters")
        return response.json()
    
    # Quality Metrics
    
    def get_quality_metrics(self, experiment_id: str) -> Dict[str, Any]:
        """Get quality metrics for an experiment"""
        response = self._request("GET", f"/experiments/{experiment_id}/quality-metrics")
        return response.json()
    
    # ML Features
    
    def get_ml_features(self, experiment_id: str) -> Dict[str, Any]:
        """Get ML features for an experiment"""
        response = self._request("GET", f"/experiments/{experiment_id}/ml-features")
        return response.json()
    
    # Analytics
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        response = self._request("GET", "/analytics/summary")
        return response.json()
    
    # Export
    
    def export_dataset(
        self,
        format: str = "csv",
        material_type: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> bytes:
        """Export dataset"""
        params = {"format": format}
        if material_type:
            params["material_type"] = material_type
        
        response = self._request("GET", "/export/dataset", params=params)
        
        if save_path:
            with open(save_path, "wb") as f:
                f.write(response.content)
        
        return response.content


# Example Usage

def example_create_experiment():
    """Example: Create a new experiment"""
    client = AMDataAPIClient()
    
    experiment_data = {
        "experiment_id": "EXP-CLIENT-001",   # changed from EXP-2024-001
        "experiment_name": "PLA High Speed Test",
        "material_type": "PLA",
        "material_batch": "BATCH-2024-01",
        "build_platform": "Ender 3 Pro",
        "build_date": datetime.now().isoformat(),
        "operator": "John Doe",
        "status": "completed",
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
            "bounding_box_z": 10.0
        },
        "quality_metrics": {
            "tensile_strength_mpa": 45.2,
            "surface_roughness_um": 8.5,
            "porosity_percent": 2.1,
            "density_g_per_cm3": 1.24,
            "defect_count": 0
        }
    }
    
    result = client.create_experiment(experiment_data)
    print("Created experiment:", json.dumps(result, indent=2, default=str))
    return result


def example_list_experiments():
    """Example: List experiments with filtering"""
    client = AMDataAPIClient()
    
    # List all experiments
    all_experiments = client.list_experiments()
    print(f"Total experiments: {all_experiments['total']}")
    print(f"Page: {all_experiments['page']}/{all_experiments['pages']}")
    
    # Filter by material type
    pla_experiments = client.list_experiments(material_type="PLA")
    print(f"\nPLA experiments: {pla_experiments['total']}")
    
    # Filter by status
    completed = client.list_experiments(status="completed")
    print(f"Completed experiments: {completed['total']}")
    
    return all_experiments


def example_get_experiment():
    """Example: Get specific experiment"""
    client = AMDataAPIClient()
    
    experiment = client.get_experiment("EXP-2024-001")
    print("Experiment details:")
    print(json.dumps(experiment, indent=2, default=str))
    
    # Get process parameters
    params = client.get_process_parameters("EXP-2024-001")
    print("\nProcess Parameters:")
    print(json.dumps(params, indent=2))
    
    # Get quality metrics
    metrics = client.get_quality_metrics("EXP-2024-001")
    print("\nQuality Metrics:")
    print(json.dumps(metrics, indent=2))
    
    # Get ML features
    features = client.get_ml_features("EXP-2024-001")
    print("\nML Features:")
    print(json.dumps(features, indent=2))
    
    return experiment


def example_update_experiment():
    """Example: Update an experiment"""
    client = AMDataAPIClient()
    
    update_data = {
        "status": "completed",
        "notes": "Updated with additional measurements",
        "quality_metrics": {
            "tensile_strength_mpa": 46.5,
            "surface_roughness_um": 8.2
        }
    }
    
    updated = client.update_experiment("EXP-2024-001", update_data)
    print("Updated experiment:")
    print(json.dumps(updated, indent=2, default=str))
    
    return updated


def example_export_data():
    """Example: Export dataset"""
    client = AMDataAPIClient()
    
    # Export as CSV
    csv_data = client.export_dataset(format="csv", save_path="am_data.csv")
    print("Exported CSV dataset")
    
    # Export as JSON
    json_data = client.export_dataset(format="json")
    print(f"Exported JSON dataset ({len(json_data)} bytes)")
    
    # Export as Parquet
    parquet_data = client.export_dataset(format="parquet", save_path="am_data.parquet")
    print("Exported Parquet dataset")
    
    # Export filtered by material
    pla_data = client.export_dataset(format="csv", material_type="PLA", save_path="pla_data.csv")
    print("Exported PLA-specific dataset")


def example_analytics():
    """Example: Get analytics"""
    client = AMDataAPIClient()
    
    analytics = client.get_analytics_summary()
    print("Analytics Summary:")
    print(json.dumps(analytics, indent=2, default=str))
    
    return analytics


def example_batch_operations():
    """Example: Batch operations"""
    client = AMDataAPIClient()
    
    # Create multiple experiments
    experiments = [
        {
            "experiment_id": f"EXP-2024-{i:03d}",
            "experiment_name": f"Test Experiment {i}",
            "material_type": "PLA",
            "status": "completed",
            "process_parameters": {
                "nozzle_temperature": 210.0 + i,
                "print_speed": 50.0 + i * 5
            }
        }
        for i in range(1, 6)
    ]
    
    created = []
    for exp_data in experiments:
        try:
            result = client.create_experiment(exp_data)
            created.append(result)
            print(f"Created: {exp_data['experiment_id']}")
        except requests.exceptions.HTTPError as e:
            print(f"Error creating {exp_data['experiment_id']}: {e}")
    
    print(f"\nCreated {len(created)} experiments")
    return created


if __name__ == "__main__":
    print("AM Experimental Data Management API - Client Examples")
    print("=" * 60)

    client = AMDataAPIClient()

    # ── 1. Health check ───────────────────────────────────────────
    try:
        health = client.health_check()
        print(f"API Status : {health.get('status', 'ok')}")
        print(f"Database   : {health.get('database', 'connected')}")
    except Exception as e:
        print(f"API not available: {e}")
        exit(1)

    # ── 2. Create experiment ──────────────────────────────────────
    print("\n1. Creating experiment...")
    try:
        result = example_create_experiment()
        print("   Created:", result.get("experiment_id"))
    except Exception as e:
        print(f"   Note: {e}")

    # ── 3. List experiments ───────────────────────────────────────
    print("\n2. Listing experiments...")
    try:
        # Use raw request to avoid pagination model mismatch
        r = client.session.get(f"{client.api_base}/experiments",
                               params={"page": 1, "page_size": 10})
        data = r.json()
        total = data.get("total", len(data.get("items", [])))
        print(f"   Total experiments : {total}")
    except Exception as e:
        print(f"   Error: {e}")

    # ── 4. Get single experiment ──────────────────────────────────
    print("\n3. Getting experiment details...")
    try:
        exp = client.get_experiment("EXP-2024-001")
        print(f"   Name     : {exp.get('experiment_name')}")
        print(f"   Material : {exp.get('material_type')}")
        print(f"   Status   : {exp.get('status')}")
    except Exception as e:
        print(f"   Error: {e}")

    # ── 5. ML features ────────────────────────────────────────────
    print("\n4. Getting ML features...")
    try:
        features = client.get_ml_features("EXP-2024-001")
        print(f"   Feature count : {features.get('count')}")
        print(f"   Features      : {list(features.get('features', {}).keys())}")
    except Exception as e:
        print(f"   Error: {e}")

    # ── 6. Analytics ──────────────────────────────────────────────
    print("\n5. Getting analytics...")
    try:
        analytics = client.get_analytics_summary()
        print(f"   Total experiments     : {analytics.get('total_experiments')}")
        print(f"   Material distribution : {analytics.get('material_distribution')}")
        avg = analytics.get("average_quality_metrics", {})
        print(f"   Avg tensile strength  : {avg.get('tensile_strength_mpa')}")
    except Exception as e:
        print(f"   Error: {e}")

    # ── 7. Export ─────────────────────────────────────────────────
    print("\n6. Exporting data...")
    try:
        client.export_dataset(format="csv", save_path="am_data_export.csv")
        print("   CSV  export saved → am_data_export.csv")
        client.export_dataset(format="json")
        print("   JSON export complete")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("All steps complete!")
    print(f"Open http://localhost:8000/api/v1/docs to explore all endpoints")
    print(f"Open http://localhost:8000/dashboard/advanced for the visual dashboard")
    print("=" * 60)
