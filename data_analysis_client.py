"""
Data Analysis Client Examples
Demonstrates how to use the data analysis API
"""

import requests
import json
from typing import Optional, List, Dict, Any
import base64
from io import BytesIO
from PIL import Image

class DataAnalysisClient:
    """Client for data analysis operations"""
    
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
    
    def explore_data(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        include_visualizations: bool = True
    ) -> Dict[str, Any]:
        """Perform exploratory data analysis"""
        data = {
            "include_visualizations": include_visualizations
        }
        if experiment_ids:
            data["experiment_ids"] = experiment_ids # type: ignore
        if material_type:
            data["material_type"] = material_type # type: ignore
        
        response = self._request("POST", "/analysis/explore", json=data)
        return response.json()
    
    def create_visualization(
        self,
        plot_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        color_by: Optional[str] = None,
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create visualization"""
        data = {
            "plot_type": plot_type,
            "x_column": x_column,
            "y_column": y_column,
            "color_by": color_by,
            "columns": columns,
            "title": title
        }
        
        params = {}
        if material_type:
            params["material_type"] = material_type
        
        if experiment_ids:
            data["experiment_ids"] = experiment_ids
        
        response = self._request("POST", "/analysis/visualize", json=data, params=params)
        return response.json()
    
    def get_statistics(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistical summary"""
        params = {}
        if experiment_ids:
            params["experiment_ids"] = experiment_ids
        if material_type:
            params["material_type"] = material_type
        
        response = self._request("GET", "/analysis/statistics", params=params)
        return response.json()
    
    def get_correlations(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Get correlation analysis"""
        params = {"threshold": threshold}
        if experiment_ids:
            params["experiment_ids"] = experiment_ids # type: ignore
        if material_type:
            params["material_type"] = material_type # type: ignore
        
        response = self._request("GET", "/analysis/correlations", params=params)
        return response.json()
    
    def perform_pca(
        self,
        experiment_ids: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        n_components: int = 2
    ) -> Dict[str, Any]:
        """Perform PCA"""
        data = {}
        if experiment_ids:
            data["experiment_ids"] = experiment_ids
        
        params = {"n_components": n_components}
        if material_type:
            params["material_type"] = material_type # type: ignore
        
        response = self._request("POST", "/analysis/pca", json=data, params=params)
        return response.json()
    
    def save_visualization(self, viz_data: Dict[str, Any], filename: str):
        """Save visualization image to file"""
        if "image" in viz_data:
            img_data = base64.b64decode(viz_data["image"])
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"Visualization saved to {filename}")
        else:
            print("No image data in visualization")


# Example Usage

def example_explore_data():
    """Example: Exploratory data analysis"""
    client = DataAnalysisClient()
    
    result = client.explore_data(material_type="PLA", include_visualizations=True)
    
    print("Exploratory Data Analysis Results")
    print("=" * 60)
    
    report = result["report"]
    print(f"\nTotal Experiments: {result['data_summary']['total_experiments']}")
    print(f"Overall Insights: {len(report['insights'])}")
    print(f"Recommendations: {len(report['recommendations'])}")
    
    print("\nInsights:")
    for insight in report['insights'][:5]:
        print(f"  - {insight}")
    
    print("\nRecommendations:")
    for rec in report['recommendations'][:5]:
        print(f"  - {rec}")
    
    # Save visualizations
    if "visualizations" in result:
        if "correlation_heatmap" in result["visualizations"]:
            client.save_visualization(
                result["visualizations"]["correlation_heatmap"],
                "correlation_heatmap.png"
            )
        if "summary_dashboard" in result["visualizations"]:
            client.save_visualization(
                result["visualizations"]["summary_dashboard"],
                "summary_dashboard.png"
            )
    
    return result


def example_create_visualizations():
    """Example: Create various visualizations"""
    client = DataAnalysisClient()
    
    # Scatter plot
    print("Creating scatter plot...")
    scatter = client.create_visualization(
        plot_type="scatter",
        x_column="nozzle_temperature",
        y_column="tensile_strength_mpa",
        color_by="infill_percentage",
        material_type="PLA",
        title="Temperature vs Strength"
    )
    client.save_visualization(scatter, "scatter_plot.png")
    
    # Correlation heatmap
    print("Creating correlation heatmap...")
    heatmap = client.create_visualization(
        plot_type="heatmap",
        material_type="PLA"
    )
    client.save_visualization(heatmap, "correlation_heatmap.png")
    
    # Distribution plot
    print("Creating distribution plot...")
    dist = client.create_visualization(
        plot_type="distribution",
        x_column="tensile_strength_mpa",
        material_type="PLA"
    )
    client.save_visualization(dist, "distribution.png")
    
    # Summary dashboard
    print("Creating summary dashboard...")
    dashboard = client.create_visualization(
        plot_type="dashboard",
        material_type="PLA",
        title="PLA Data Summary"
    )
    client.save_visualization(dashboard, "dashboard.png")
    
    return scatter, heatmap, dist, dashboard


def example_statistical_analysis():
    """Example: Statistical analysis"""
    client = DataAnalysisClient()
    
    stats = client.get_statistics(material_type="PLA")
    
    print("Statistical Summary")
    print("=" * 60)
    
    for field, stat_data in stats["statistics"].items():
        print(f"\n{field}:")
        print(f"  Mean: {stat_data['mean']:.2f}")
        print(f"  Std: {stat_data['std']:.2f}")
        print(f"  Min: {stat_data['min']:.2f}")
        print(f"  Max: {stat_data['max']:.2f}")
        print(f"  Median: {stat_data['q50']:.2f}")
    
    return stats


def example_correlation_analysis():
    """Example: Correlation analysis"""
    client = DataAnalysisClient()
    
    corr = client.get_correlations(material_type="PLA", threshold=0.6)
    
    print("Correlation Analysis")
    print("=" * 60)
    
    print(f"\nStrong Correlations (threshold: 0.6):")
    for pair in corr["strong_correlations"][:10]:
        print(f"  {pair['variable1']} <-> {pair['variable2']}: {pair['correlation']:.3f}")
    
    print(f"\nSignificant Pairs (p < 0.05):")
    for pair in corr["significant_pairs"][:10]:
        print(f"  {pair['variable1']} <-> {pair['variable2']}: {pair['correlation']:.3f} (p={pair['p_value']:.4f})")
    
    return corr


def example_pca_analysis():
    """Example: PCA analysis"""
    client = DataAnalysisClient()
    
    pca_result = client.perform_pca(material_type="PLA", n_components=2)
    
    if "error" in pca_result:
        print(f"PCA Error: {pca_result['error']}")
        return pca_result
    
    print("PCA Analysis")
    print("=" * 60)
    
    print(f"\nExplained Variance:")
    for i, var in enumerate(pca_result["explained_variance_ratio"]):
        print(f"  PC{i+1}: {var:.1%}")
    
    print(f"\nCumulative Variance:")
    for i, var in enumerate(pca_result["cumulative_variance"]):
        print(f"  PC{i+1}: {var:.1%}")
    
    # Save visualization if available
    if "visualization" in pca_result:
        client.save_visualization(pca_result["visualization"], "pca_analysis.png")
    
    return pca_result


if __name__ == "__main__":
    print("Data Analysis Pipeline - Client Examples")
    print("=" * 60)
    
    client = DataAnalysisClient()
    
    try:
        # Test connection
        response = requests.get(f"{client.api_base}/health")
        print(f"API Status: {response.json()['status']}")
    except Exception as e:
        print(f"API not available: {e}")
        exit(1)
    
    print("\n1. Exploratory Data Analysis...")
    example_explore_data()
    
    print("\n2. Statistical Analysis...")
    example_statistical_analysis()
    
    print("\n3. Correlation Analysis...")
    example_correlation_analysis()
    
    print("\n4. Creating Visualizations...")
    example_create_visualizations()
    
    print("\n5. PCA Analysis...")
    example_pca_analysis()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
