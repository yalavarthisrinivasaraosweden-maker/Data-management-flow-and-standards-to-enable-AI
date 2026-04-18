"""
Version Control Client Examples
Demonstrates how to use the version control API
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

class VersionControlClient:
    """Client for version control operations"""
    
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
    
    def create_version(
        self,
        experiment_id: str,
        created_by: str,
        change_type: str,
        change_description: Optional[str] = None,
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """Create a version snapshot"""
        data = {
            "created_by": created_by,
            "change_type": change_type,
            "change_description": change_description,
            "tags": tags or []
        }
        response = self._request("POST", f"/experiments/{experiment_id}/versions", json=data)
        return response.json()
    
    def get_version_history(self, experiment_id: str) -> Dict[str, Any]:
        """Get version history for an experiment"""
        response = self._request("GET", f"/experiments/{experiment_id}/versions")
        return response.json()
    
    def get_version_snapshot(self, version_id: int) -> Dict[str, Any]:
        """Get full snapshot for a version"""
        response = self._request("GET", f"/versions/{version_id}")
        return response.json()
    
    def restore_version(
        self,
        version_id: int,
        restored_by: str,
        create_new_version: bool = True
    ) -> Dict[str, Any]:
        """Restore experiment to a specific version"""
        data = {
            "restored_by": restored_by,
            "create_new_version": create_new_version
        }
        response = self._request("POST", f"/versions/{version_id}/restore", json=data)
        return response.json()
    
    def compare_versions(self, version1_id: int, version2_id: int) -> Dict[str, Any]:
        """Compare two versions"""
        response = self._request("GET", f"/versions/{version1_id}/compare/{version2_id}")
        return response.json()
    
    def list_versions(
        self,
        experiment_id: Optional[str] = None,
        created_by: Optional[str] = None,
        change_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all versions with filtering"""
        params = {
            "limit": limit,
            "offset": offset
        }
        if experiment_id:
            params["experiment_id"] = experiment_id
        if created_by:
            params["created_by"] = created_by
        if change_type:
            params["change_type"] = change_type
        if tag:
            params["tag"] = tag
        
        response = self._request("GET", "/versions", params=params)
        return response.json()
    
    def add_tag(self, version_id: int, tag_name: str, tag_value: Optional[str] = None) -> Dict[str, Any]:
        """Add tag to version"""
        data = {"tag_name": tag_name, "tag_value": tag_value}
        response = self._request("POST", f"/versions/{version_id}/tags", json=data)
        return response.json()
    
    def remove_tag(self, version_id: int, tag_name: str) -> Dict[str, Any]:
        """Remove tag from version"""
        response = self._request("DELETE", f"/versions/{version_id}/tags/{tag_name}")
        return response.json()


# Example Usage

def example_create_version():
    """Example: Create a version snapshot"""
    client = VersionControlClient()
    
    version = client.create_version(
        experiment_id="EXP-2024-001",
        created_by="john.doe@example.com",
        change_type="update",
        change_description="Updated quality metrics after re-measurement",
        tags=["quality-review", "re-measurement"]
    )
    
    print("Created version:")
    print(json.dumps(version, indent=2, default=str))
    return version


def example_get_history():
    """Example: Get version history"""
    client = VersionControlClient()
    
    history = client.get_version_history("EXP-2024-001")
    
    print(f"Version History for {history['experiment_id']}:")
    print(f"Total versions: {history['total_versions']}")
    print(f"Current version: {history['current_version']}")
    print("\nVersions:")
    for v in history['versions']:
        print(f"  Version {v['version_number']}: {v['change_type']} by {v['created_by']} at {v['created_at']}")
        if v['change_description']:
            print(f"    Description: {v['change_description']}")
        if v['tags']:
            print(f"    Tags: {', '.join(v['tags'])}")
    
    return history


def example_compare_versions():
    """Example: Compare two versions"""
    client = VersionControlClient()
    
    # Get version history first
    history = client.get_version_history("EXP-2024-001")
    if len(history['versions']) < 2:
        print("Need at least 2 versions to compare")
        return
    
    v1_id = history['versions'][0]['version_id']
    v2_id = history['versions'][1]['version_id']
    
    diff = client.compare_versions(v1_id, v2_id)
    
    print(f"Comparing versions {diff['version1_id']} and {diff['version2_id']}:")
    print(f"Modified fields: {len(diff['modified_fields'])}")
    print(f"Added fields: {len(diff['added_fields'])}")
    print(f"Removed fields: {len(diff['removed_fields'])}")
    
    print("\nDifferences:")
    for field, changes in diff['differences'].items():
        print(f"  {field}:")
        print(f"    Old: {changes['old_value']}")
        print(f"    New: {changes['new_value']}")
    
    return diff


def example_restore_version():
    """Example: Restore to a previous version"""
    client = VersionControlClient()
    
    # Get version history
    history = client.get_version_history("EXP-2024-001")
    if len(history['versions']) < 2:
        print("Need at least 2 versions to restore")
        return
    
    # Restore to second most recent version
    version_to_restore = history['versions'][1]
    
    result = client.restore_version(
        version_id=version_to_restore['version_id'],
        restored_by="admin@example.com",
        create_new_version=True
    )
    
    print("Restore result:")
    print(json.dumps(result, indent=2, default=str))
    return result


def example_tag_management():
    """Example: Tag management"""
    client = VersionControlClient()
    
    # Get a version
    history = client.get_version_history("EXP-2024-001")
    if not history['versions']:
        print("No versions found")
        return
    
    version_id = history['versions'][0]['version_id']
    
    # Add tags
    client.add_tag(version_id, "production-ready")
    client.add_tag(version_id, "validated")
    
    # Get updated version
    version = client.get_version_snapshot(version_id)
    print(f"Version {version_id} tags: {version.get('tags', [])}")
    
    # Remove a tag
    client.remove_tag(version_id, "production-ready")
    
    return version


def example_list_all_versions():
    """Example: List all versions with filtering"""
    client = VersionControlClient()
    
    # List all versions
    all_versions = client.list_versions(limit=10)
    print(f"Total versions: {len(all_versions)}")
    
    # Filter by experiment
    exp_versions = client.list_versions(experiment_id="EXP-2024-001")
    print(f"Versions for EXP-2024-001: {len(exp_versions)}")
    
    # Filter by creator
    user_versions = client.list_versions(created_by="john.doe@example.com")
    print(f"Versions by john.doe: {len(user_versions)}")
    
    # Filter by tag
    tagged_versions = client.list_versions(tag="production-ready")
    print(f"Versions with 'production-ready' tag: {len(tagged_versions)}")
    
    return all_versions


if __name__ == "__main__":
    print("Version Control API - Client Examples")
    print("=" * 60)
    
    client = VersionControlClient()
    
    try:
        # Test connection
        print("Testing API connection...")
        response = requests.get(f"{client.api_base}/health")
        print(f"API Status: {response.json()['status']}")
    except Exception as e:
        print(f"API not available: {e}")
        exit(1)
    
    print("\n1. Creating version snapshot...")
    example_create_version()
    
    print("\n2. Getting version history...")
    example_get_history()
    
    print("\n3. Comparing versions...")
    example_compare_versions()
    
    print("\n4. Tag management...")
    example_tag_management()
    
    print("\n5. Listing all versions...")
    example_list_all_versions()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
