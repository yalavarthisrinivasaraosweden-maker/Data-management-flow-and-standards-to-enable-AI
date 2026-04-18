"""
Visualization Generator
Generate various types of visualizations for data exploration
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import json
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class VisualizationGenerator:
    """Generate visualizations for data analysis"""
    
    def __init__(self):
        self.figures = []
    
    def _fig_to_base64(self, fig: Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    def create_scatter_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        color_by: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create scatter plot"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if color_by and color_by in df.columns:
            scatter = ax.scatter(df[x], df[y], c=df[color_by], cmap='viridis', alpha=0.6)
            plt.colorbar(scatter, ax=ax, label=color_by)
        else:
            ax.scatter(df[x], df[y], alpha=0.6)
        
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(title or f"{y} vs {x}")
        ax.grid(True, alpha=0.3)
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "scatter",
            "x": x,
            "y": y,
            "image": img_base64,
            "data_points": len(df)
        }
    
    def create_correlation_heatmap(
        self,
        df: pd.DataFrame,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create correlation heatmap"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {"error": "Insufficient numeric columns"}
        
        fig, ax = plt.subplots(figsize=(12, 10))
        corr_matrix = df[numeric_cols].corr()
        
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            ax=ax,
            cbar_kws={"shrink": 0.8}
        )
        
        ax.set_title(title or "Correlation Heatmap")
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "heatmap",
            "image": img_base64,
            "variables": numeric_cols
        }
    
    def create_distribution_plot(
        self,
        df: pd.DataFrame,
        column: str,
        plot_type: str = "histogram"  # "histogram", "kde", "box"
    ) -> Dict[str, Any]:
        """Create distribution plot"""
        if column not in df.columns:
            return {"error": f"Column {column} not found"}
        
        values = df[column].dropna()
        if len(values) == 0:
            return {"error": "No data available"}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if plot_type == "histogram":
            ax.hist(values, bins=20, alpha=0.7, edgecolor='black')
            ax.set_xlabel(column)
            ax.set_ylabel("Frequency")
            ax.set_title(f"Distribution of {column}")
        
        elif plot_type == "kde":
            from scipy.stats import gaussian_kde
            try:
                kde = gaussian_kde(values)
                x_range = np.linspace(values.min(), values.max(), 100)
                ax.plot(x_range, kde(x_range), linewidth=2)
                ax.fill_between(x_range, kde(x_range), alpha=0.3)
                ax.set_xlabel(column)
                ax.set_ylabel("Density")
                ax.set_title(f"KDE of {column}")
            except:
                return {"error": "KDE calculation failed"}
        
        elif plot_type == "box":
            ax.boxplot(values, vert=True)
            ax.set_ylabel(column)
            ax.set_title(f"Box Plot of {column}")
        
        ax.grid(True, alpha=0.3)
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": plot_type,
            "column": column,
            "image": img_base64,
            "statistics": {
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max())
            }
        }
    
    def create_time_series_plot(
        self,
        df: pd.DataFrame,
        time_column: str,
        value_column: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create time series plot"""
        if time_column not in df.columns or value_column not in df.columns:
            return {"error": "Required columns not found"}
        
        # Convert time column to datetime if needed
        df_plot = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_plot[time_column]):
            df_plot[time_column] = pd.to_datetime(df_plot[time_column], errors='coerce')
        
        df_plot = df_plot.sort_values(time_column).dropna(subset=[time_column, value_column])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_plot[time_column], df_plot[value_column], marker='o', linewidth=2, markersize=4)
        ax.set_xlabel(time_column)
        ax.set_ylabel(value_column)
        ax.set_title(title or f"{value_column} over Time")
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "time_series",
            "time_column": time_column,
            "value_column": value_column,
            "image": img_base64,
            "data_points": len(df_plot)
        }
    
    def create_pair_plot(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Create pair plot (scatter matrix)"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if columns:
            numeric_cols = [c for c in columns if c in numeric_cols]
        
        if len(numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns"}
        
        # Limit columns for performance
        if len(numeric_cols) > 6:
            numeric_cols = numeric_cols[:6]
        
        # Sample data if too large
        df_plot = df[numeric_cols].dropna()
        if len(df_plot) > sample_size:
            df_plot = df_plot.sample(n=sample_size, random_state=42)
        
        fig = sns.pairplot(df_plot, diag_kind='kde', plot_kws={'alpha': 0.6})
        fig.fig.suptitle("Pair Plot", y=1.02)
        
        img_base64 = self._fig_to_base64(fig.fig)
        
        return {
            "type": "pair_plot",
            "image": img_base64,
            "columns": numeric_cols,
            "sample_size": len(df_plot)
        }
    
    def create_cluster_visualization(
        self,
        df: pd.DataFrame,
        cluster_labels: List[int],
        x_col: str,
        y_col: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create cluster visualization"""
        if x_col not in df.columns or y_col not in df.columns:
            return {"error": "Required columns not found"}
        
        if len(cluster_labels) != len(df):
            return {"error": "Cluster labels length mismatch"}
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        unique_clusters = sorted(set(cluster_labels))
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_clusters)))
        
        for i, cluster in enumerate(unique_clusters):
            mask = np.array(cluster_labels) == cluster
            ax.scatter(
                df[x_col][mask],
                df[y_col][mask],
                c=[colors[i]],
                label=f"Cluster {cluster}",
                alpha=0.6,
                s=50
            )
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title or "Cluster Visualization")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "cluster",
            "image": img_base64,
            "n_clusters": len(unique_clusters),
            "x": x_col,
            "y": y_col
        }
    
    def create_pca_visualization(
        self,
        pca_result: Dict[str, Any],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create PCA visualization"""
        if "error" in pca_result:
            return pca_result
        
        components = pca_result["components"]
        if len(components[0]) < 2:
            return {"error": "Need at least 2 components"}
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Scatter plot of first two components
        pc1 = [c[0] for c in components]
        pc2 = [c[1] if len(c) > 1 else 0 for c in components]
        
        ax1.scatter(pc1, pc2, alpha=0.6)
        ax1.set_xlabel(f"PC1 ({pca_result['explained_variance_ratio'][0]:.1%} variance)")
        ax1.set_ylabel(f"PC2 ({pca_result['explained_variance_ratio'][1]:.1%} variance)")
        ax1.set_title("PCA Scatter Plot")
        ax1.grid(True, alpha=0.3)
        
        # Explained variance
        ax2.bar(
            range(1, len(pca_result['explained_variance_ratio']) + 1),
            pca_result['explained_variance_ratio'],
            alpha=0.7
        )
        ax2.plot(
            range(1, len(pca_result['cumulative_variance']) + 1),
            pca_result['cumulative_variance'],
            'ro-',
            label='Cumulative'
        )
        ax2.set_xlabel("Principal Component")
        ax2.set_ylabel("Explained Variance Ratio")
        ax2.set_title("Explained Variance")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        fig.suptitle(title or "PCA Analysis", y=1.02)
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "pca",
            "image": img_base64,
            "n_components": pca_result["n_components"],
            "explained_variance": pca_result["explained_variance_ratio"]
        }
    
    def create_summary_dashboard(
        self,
        df: pd.DataFrame,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create summary dashboard with multiple plots"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) == 0:
            return {"error": "No numeric columns available"}
        
        # Create subplots
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        axes = axes.flatten()
        
        for i, col in enumerate(numeric_cols[:n_rows * n_cols]):
            ax = axes[i]
            values = df[col].dropna()
            ax.hist(values, bins=20, alpha=0.7, edgecolor='black')
            ax.set_title(f"{col}\n(mean={values.mean():.2f}, std={values.std():.2f})")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(len(numeric_cols), len(axes)):
            axes[i].axis('off')
        
        fig.suptitle(title or "Data Summary Dashboard", y=1.02, fontsize=16)
        plt.tight_layout()
        
        img_base64 = self._fig_to_base64(fig)
        
        return {
            "type": "dashboard",
            "image": img_base64,
            "columns": numeric_cols
        }
