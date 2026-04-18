"""
Data Quality Client Examples
Demonstrates how to use the data quality API
"""

import requests
import json
from typing import Optional, List, Dict, Any

class DataQualityClient:
    """Client for data quality operations"""
    
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
        response.raise_for_status()
        return response
    
    def validate_experiment(
        self,
        experiment_id: Optional[str] = None,
        experiments: Optional[List[Dict]] = None,
        validation_level: str = "moderate"
    ) -> Dict[str, Any]:
        """Validate experiment(s)"""
        data = {
            "validation_level": validation_level
        }
        if experiment_id:
            data["experiment_id"] = experiment_id
        if experiments:
            data["experiments"] = experiments # type: ignore
        
        response = self._request("POST", "/data-quality/validate", json=data)
        return response.json()
    
    def clean_dataset(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        remove_outliers: bool = True,
        handle_missing: bool = True,
        remove_duplicates: bool = True,
        normalize: bool = False
    ) -> Dict[str, Any]:
        """Clean dataset"""
        params = {}
        if material_type:
            params["material_type"] = material_type
        
        data = {
            "remove_outliers": remove_outliers,
            "handle_missing": handle_missing,
            "remove_duplicates": remove_duplicates,
            "normalize": normalize
        }
        
        if experiment_ids:
            data["experiment_ids"] = experiment_ids # type: ignore
        
        response = self._request("POST", "/data-quality/clean", json=data, params=params)
        return response.json()
    
    def preprocess_dataset(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        normalize: bool = True,
        feature_engineering: bool = True
    ) -> Dict[str, Any]:
        """Preprocess dataset"""
        params = {}
        if material_type:
            params["material_type"] = material_type
        
        data = {
            "normalize": normalize,
            "feature_engineering": feature_engineering
        }
        
        if experiment_ids:
            data["experiment_ids"] = experiment_ids # type: ignore
        
        response = self._request("POST", "/data-quality/preprocess", json=data, params=params)
        return response.json()
    
    def get_quality_issues(
        self,
        experiment_id: Optional[str] = None,
        material_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get data quality issues"""
        params = {}
        if experiment_id:
            params["experiment_id"] = experiment_id
        if material_type:
            params["material_type"] = material_type
        if severity:
            params["severity"] = severity
        
        response = self._request("GET", "/data-quality/issues", params=params)
        return response.json()


# Example Usage

def example_validate_experiment():
    """Example: Validate an experiment"""
    client = DataQualityClient()
    
    # Validate single experiment
    report = client.validate_experiment(
        experiment_id="EXP-2024-001",
        validation_level="moderate"
    )
    
    print("Data Quality Report:")
    print(f"Overall Score: {report['overall_score']:.2%}")
    print(f"Completeness: {report['completeness_score']:.2%}")
    print(f"Validity: {report['validity_score']:.2%}")
    print(f"Consistency: {report['consistency_score']:.2%}")
    print(f"\nTotal Issues: {len(report['issues'])}")
    
    # Show issues
    errors = [i for i in report['issues'] if i['severity'] == 'error']
    warnings = [i for i in report['issues'] if i['severity'] == 'warning']
    
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    
    if errors:
        print("\nErrors:")
        for error in errors[:5]:  # Show first 5
            print(f"  - {error['field']}: {error['message']}")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings[:5]:  # Show first 5
            print(f"  - {warning['field']}: {warning['message']}")
    
    return report


def example_clean_dataset():
    """Example: Clean dataset"""
    client = DataQualityClient()
    
    result = client.clean_dataset(
        material_type="PLA",
        remove_outliers=True,
        handle_missing=True,
        remove_duplicates=True,
        normalize=False
    )
    
    print("Cleaning Results:")
    print(f"Initial rows: {result['statistics']['initial_rows']}")
    print(f"Final rows: {result['statistics']['final_rows']}")
    print(f"Removed rows: {result['statistics']['removed_rows']}")
    
    print("\nCleaning Steps:")
    for step in result['cleaning_log']['steps']:
        print(f"  - {step['step']}: {step.get('removed', step.get('filled', 'N/A'))}")
    
    return result


def example_preprocess_dataset():
    """Example: Preprocess dataset"""
    client = DataQualityClient()
    
    result = client.preprocess_dataset(
        material_type="PLA",
        normalize=True,
        feature_engineering=True
    )
    
    print("Preprocessing Results:")
    print(f"Features: {len(result['preprocessed_data'][0].keys())}")
    print(f"Normalized: {result['preprocessing_info']['normalized']}")
    print(f"Feature Engineering: {result['preprocessing_info']['feature_engineering']}")
    
    print("\nSample preprocessed record:")
    print(json.dumps(result['preprocessed_data'][0], indent=2, default=str))
    
    return result


def example_get_issues():
    """Example: Get quality issues"""
    client = DataQualityClient()
    
    issues = client.get_quality_issues(
        material_type="PLA",
        severity="error"
    )
    
    print(f"Total Issues: {issues['total_issues']}")
    
    if issues['issues']:
        print("\nIssues:")
        for issue in issues['issues'][:10]:  # Show first 10
            print(f"  [{issue['severity'].upper()}] {issue['field']}: {issue['message']}")
            if issue.get('suggestion'):
                print(f"    Suggestion: {issue['suggestion']}")
    
    return issues


if __name__ == "__main__":
    print("Data Quality Pipeline - Client Examples")
    print("=" * 60)
    
    client = DataQualityClient()
    
    try:
        # Test connection
        response = requests.get(f"{client.api_base}/health")
        print(f"API Status: {response.json()['status']}")
    except Exception as e:
        print(f"API not available: {e}")
        exit(1)
    
    print("\n1. Validating experiment...")
    example_validate_experiment()
    
    print("\n2. Cleaning dataset...")
    example_clean_dataset()
    
    print("\n3. Preprocessing dataset...")
    example_preprocess_dataset()
    
    print("\n4. Getting quality issues...")
    example_get_issues()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
