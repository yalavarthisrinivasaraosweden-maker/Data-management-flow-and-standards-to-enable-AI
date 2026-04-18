"""
Data Analysis and Visualization Pipeline
Comprehensive data exploration and discovery system for AM experimental data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import json
import warnings
warnings.filterwarnings('ignore')

class StatisticalSummary(BaseModel):
    """Statistical summary of a dataset"""
    count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q25: Optional[float] = None
    q50: Optional[float] = None
    q75: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

class CorrelationAnalysis(BaseModel):
    """Correlation analysis results"""
    correlation_matrix: Dict[str, Dict[str, float]]
    strong_correlations: List[Dict[str, Any]]
    weak_correlations: List[Dict[str, Any]]
    significant_pairs: List[Dict[str, Any]]

class DistributionAnalysis(BaseModel):
    """Distribution analysis results"""
    field: str
    distribution_type: str  # 'normal', 'skewed', 'bimodal', etc.
    normality_test: Dict[str, float]
    histogram_data: Dict[str, Any]
    kde_data: Optional[Dict[str, Any]] = None

class PatternDiscovery(BaseModel):
    """Pattern discovery results"""
    clusters: Optional[Dict[str, Any]] = None
    anomalies: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

class AnalysisReport(BaseModel):
    """Comprehensive analysis report"""
    experiment_ids: List[str]
    timestamp: datetime
    statistical_summary: Dict[str, StatisticalSummary]
    correlation_analysis: CorrelationAnalysis
    distribution_analysis: List[DistributionAnalysis]
    pattern_discovery: PatternDiscovery
    insights: List[str]
    recommendations: List[str]

class DataAnalysisPipeline:
    """Main data analysis pipeline"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def generate_statistical_summary(self, df: pd.DataFrame) -> Dict[str, StatisticalSummary]:
        """Generate statistical summary for all numeric columns"""
        summary = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            values = df[col].dropna()
            if len(values) == 0:
                continue
            
            summary[col] = StatisticalSummary(
                count=len(values),
                mean=float(values.mean()),
                std=float(values.std()) if len(values) > 1 else None,
                min=float(values.min()),
                max=float(values.max()),
                q25=float(values.quantile(0.25)),
                q50=float(values.median()),
                q75=float(values.quantile(0.75)),
                skewness=float(stats.skew(values)) if len(values) > 2 else None,
                kurtosis=float(stats.kurtosis(values)) if len(values) > 2 else None
            )
        
        return summary
    
    def analyze_correlations(
        self,
        df: pd.DataFrame,
        threshold: float = 0.7,
        method: str = "pearson"
    ) -> CorrelationAnalysis:
        """Analyze correlations between variables"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return CorrelationAnalysis(
                correlation_matrix={},
                strong_correlations=[],
                weak_correlations=[],
                significant_pairs=[]
            )
        
        corr_matrix = df[numeric_cols].corr(method=method) # type: ignore
        
        # Convert to dict
        corr_dict = {}
        for col1 in corr_matrix.columns:
            corr_dict[col1] = {}
            for col2 in corr_matrix.columns:
                corr_dict[col1][col2] = float(corr_matrix.loc[col1, col2]) # type: ignore
        
        # Find strong correlations
        strong_correlations = []
        weak_correlations = []
        
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates
                    corr_value = corr_matrix.loc[col1, col2]
                    if abs(corr_value) >= threshold: # type: ignore
                        strong_correlations.append({
                            "variable1": col1,
                            "variable2": col2,
                            "correlation": float(corr_value), # type: ignore
                            "strength": "strong" if abs(corr_value) >= 0.8 else "moderate" # type: ignore
                        })
                    elif abs(corr_value) < 0.3: # type: ignore
                        weak_correlations.append({
                            "variable1": col1,
                            "variable2": col2,
                            "correlation": float(corr_value) # type: ignore
                        })
        
        # Statistical significance
        significant_pairs = []
        for col1 in corr_matrix.columns:
            for col2 in corr_matrix.columns:
                if col1 != col2:
                    try:
                        x = df[col1].dropna()
                        y = df[col2].dropna()
                        common_idx = x.index.intersection(y.index)
                        if len(common_idx) > 3:
                            corr_coef, p_value = stats.pearsonr(
                                x.loc[common_idx],
                                y.loc[common_idx]
                            )
                            if p_value < 0.05: # type: ignore
                                significant_pairs.append({
                                    "variable1": col1,
                                    "variable2": col2,
                                    "correlation": float(corr_coef), # type: ignore
                                    "p_value": float(p_value), # type: ignore
                                    "significant": True
                                })
                    except:
                        pass
        
        return CorrelationAnalysis(
            correlation_matrix=corr_dict,
            strong_correlations=strong_correlations,
            weak_correlations=weak_correlations,
            significant_pairs=significant_pairs
        )
    
    def analyze_distributions(self, df: pd.DataFrame) -> List[DistributionAnalysis]:
        """Analyze distributions of numeric variables"""
        distributions = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            values = df[col].dropna()
            if len(values) < 3:
                continue
            
            # Normality test
            try:
                stat, p_value = stats.normaltest(values)
                is_normal = p_value > 0.05
            except:
                stat, p_value = None, None
                is_normal = False
            
            # Determine distribution type
            skew = stats.skew(values)
            if abs(skew) < 0.5 and is_normal:
                dist_type = "normal"
            elif abs(skew) > 1:
                dist_type = "highly_skewed"
            elif abs(skew) > 0.5:
                dist_type = "skewed"
            else:
                dist_type = "approximately_normal"
            
            # Histogram data
            hist, bins = np.histogram(values, bins=20)
            histogram_data = {
                "bins": [float(b) for b in bins],
                "counts": [int(c) for c in hist]
            }
            
            # KDE data
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(values)
                x_kde = np.linspace(values.min(), values.max(), 100)
                y_kde = kde(x_kde)
                kde_data = {
                    "x": [float(x) for x in x_kde],
                    "y": [float(y) for y in y_kde]
                }
            except:
                kde_data = None
            
            distributions.append(DistributionAnalysis(
                field=col,
                distribution_type=dist_type,
                normality_test={
                    "statistic": float(stat) if stat else None,
                    "p_value": float(p_value) if p_value else None,
                    "is_normal": is_normal
                }, # type: ignore
                histogram_data=histogram_data,
                kde_data=kde_data
            ))
        
        return distributions
    
    def discover_patterns(
        self,
        df: pd.DataFrame,
        n_clusters: int = 3,
        anomaly_threshold: float = 2.5
    ) -> PatternDiscovery:
        """Discover patterns in data"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return PatternDiscovery(
                clusters=None,
                anomalies=[],
                trends=[],
                relationships=[]
            )
        
        # Prepare data
        data = df[numeric_cols].dropna()
        if len(data) < n_clusters:
            return PatternDiscovery(
                clusters=None,
                anomalies=[],
                trends=[],
                relationships=[]
            )
        
        # Clustering
        try:
            scaled_data = self.scaler.fit_transform(data)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(scaled_data)
            
            cluster_info = {
                "n_clusters": n_clusters,
                "cluster_labels": [int(c) for c in clusters],
                "cluster_centers": [[float(x) for x in center] for center in kmeans.cluster_centers_],
                "features": numeric_cols,
                "inertia": float(kmeans.inertia_)
            }
        except Exception as e:
            cluster_info = None
        
        # Anomaly detection
        anomalies = []
        for idx, row in data.iterrows():
            z_scores = np.abs(stats.zscore(row))
            if any(z_scores > anomaly_threshold):
                anomalies.append({
                    "index": str(idx),
                    "values": {col: float(row[col]) for col in numeric_cols},
                    "z_scores": {col: float(z_scores[i]) for i, col in enumerate(numeric_cols)},
                    "max_z_score": float(z_scores.max())
                })
        
        # Trend analysis
        trends = []
        for col in numeric_cols:
            values = data[col].values
            if len(values) > 2:
                # Linear trend
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                trends.append({
                    "field": col,
                    "trend": "increasing" if slope > 0 else "decreasing", # type: ignore
                    "slope": float(slope), # type: ignore
                    "r_squared": float(r_value ** 2), # type: ignore
                    "p_value": float(p_value), # type: ignore
                    "significant": p_value < 0.05 # type: ignore
                })
        
        # Relationship discovery
        relationships = []
        corr_analysis = self.analyze_correlations(df, threshold=0.5)
        for pair in corr_analysis.strong_correlations:
            relationships.append({
                "type": "correlation",
                "variables": [pair["variable1"], pair["variable2"]],
                "strength": pair["strength"],
                "correlation": pair["correlation"]
            })
        
        return PatternDiscovery(
            clusters=cluster_info,
            anomalies=anomalies[:50],  # Limit to 50 anomalies
            trends=trends,
            relationships=relationships
        )
    
    def perform_pca(
        self,
        df: pd.DataFrame,
        n_components: int = 2
    ) -> Dict[str, Any]:
        """Perform Principal Component Analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {"error": "Insufficient numeric columns"}
        
        data = df[numeric_cols].dropna()
        if len(data) < n_components:
            return {"error": "Insufficient data points"}
        
        # Standardize
        scaled_data = self.scaler.fit_transform(data)
        
        # PCA
        pca = PCA(n_components=min(n_components, len(numeric_cols)))
        pca_result = pca.fit_transform(scaled_data)
        
        return {
            "components": pca_result.tolist(),
            "explained_variance_ratio": [float(v) for v in pca.explained_variance_ratio_],
            "cumulative_variance": [float(v) for v in np.cumsum(pca.explained_variance_ratio_)],
            "feature_contributions": {
                col: [float(v) for v in pca.components_[i]] 
                for i, col in enumerate(numeric_cols[:n_components])
            },
            "n_components": n_components
        }
    
    def generate_insights(
        self,
        statistical_summary: Dict[str, StatisticalSummary],
        correlation_analysis: CorrelationAnalysis,
        pattern_discovery: PatternDiscovery
    ) -> List[str]:
        """Generate insights from analysis"""
        insights = []
        
        # Correlation insights
        if correlation_analysis.strong_correlations:
            top_corr = correlation_analysis.strong_correlations[0]
            insights.append(
                f"Strong correlation ({top_corr['correlation']:.2f}) found between "
                f"{top_corr['variable1']} and {top_corr['variable2']}"
            )
        
        # Distribution insights
        for field, stats_sum in statistical_summary.items():
            if stats_sum.skewness and abs(stats_sum.skewness) > 1:
                insights.append(
                    f"{field} shows significant skewness ({stats_sum.skewness:.2f}), "
                    "consider transformation"
                )
        
        # Pattern insights
        if pattern_discovery.clusters:
            insights.append(
                f"Data shows {pattern_discovery.clusters['n_clusters']} distinct clusters, "
                "suggesting multiple process regimes"
            )
        
        if pattern_discovery.anomalies:
            insights.append(
                f"Found {len(pattern_discovery.anomalies)} potential anomalies that may "
                "require investigation"
            )
        
        # Trend insights
        significant_trends = [t for t in pattern_discovery.trends if t.get("significant")]
        if significant_trends:
            insights.append(
                f"{len(significant_trends)} fields show significant trends over time"
            )
        
        return insights
    
    def generate_recommendations(
        self,
        statistical_summary: Dict[str, StatisticalSummary],
        correlation_analysis: CorrelationAnalysis,
        pattern_discovery: PatternDiscovery
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Missing data recommendations
        for field, stats_sum in statistical_summary.items():
            if stats_sum.count < len(statistical_summary) * 0.8:
                recommendations.append(
                    f"Consider collecting more data for {field} "
                    f"({stats_sum.count} observations)"
                )
        
        # Correlation recommendations
        if len(correlation_analysis.strong_correlations) > 5:
            recommendations.append(
                "Many strong correlations detected. Consider dimensionality reduction "
                "techniques like PCA"
            )
        
        # Outlier recommendations
        if pattern_discovery.anomalies:
            recommendations.append(
                f"Review {len(pattern_discovery.anomalies)} detected anomalies for "
                "data quality issues"
            )
        
        # Clustering recommendations
        if pattern_discovery.clusters:
            recommendations.append(
                "Clusters detected. Consider separate analysis for each cluster to "
                "understand process regimes"
            )
        
        return recommendations
    
    def generate_analysis_report(
        self,
        df: pd.DataFrame,
        experiment_ids: List[str]
    ) -> AnalysisReport:
        """Generate comprehensive analysis report"""
        # Statistical summary
        statistical_summary = self.generate_statistical_summary(df)
        
        # Correlation analysis
        correlation_analysis = self.analyze_correlations(df)
        
        # Distribution analysis
        distribution_analysis = self.analyze_distributions(df)
        
        # Pattern discovery
        pattern_discovery = self.discover_patterns(df)
        
        # Generate insights and recommendations
        insights = self.generate_insights(
            statistical_summary,
            correlation_analysis,
            pattern_discovery
        )
        
        recommendations = self.generate_recommendations(
            statistical_summary,
            correlation_analysis,
            pattern_discovery
        )
        
        return AnalysisReport(
            experiment_ids=experiment_ids,
            timestamp=datetime.now(),
            statistical_summary={k: v.dict() for k, v in statistical_summary.items()}, # type: ignore
            correlation_analysis=correlation_analysis.dict(), # type: ignore
            distribution_analysis=[d.dict() for d in distribution_analysis], # type: ignore
            pattern_discovery=pattern_discovery.dict(), # type: ignore
            insights=insights,
            recommendations=recommendations
        )
