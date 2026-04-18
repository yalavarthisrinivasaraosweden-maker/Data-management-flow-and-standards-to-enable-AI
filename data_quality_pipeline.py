"""
Data Cleaning and Preprocessing Pipeline
Comprehensive data quality assurance system for AM experimental data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import json
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
import warnings
warnings.filterwarnings('ignore')

class ValidationLevel(str, Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

class DataQualityIssue(BaseModel):
    """Represents a data quality issue"""
    issue_type: str
    field: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    value: Any = None
    expected_range: Optional[Dict[str, float]] = None
    suggestion: Optional[str] = None

class DataQualityReport(BaseModel):
    """Data quality assessment report"""
    experiment_id: str
    timestamp: datetime
    total_records: int
    valid_records: int
    invalid_records: int
    completeness_score: float  # 0-1
    validity_score: float  # 0-1
    consistency_score: float  # 0-1
    overall_score: float  # 0-1
    issues: List[DataQualityIssue]
    statistics: Dict[str, Any]
    recommendations: List[str]

class ValidationRule(BaseModel):
    """Data validation rule"""
    field: str
    rule_type: str  # 'range', 'regex', 'type', 'custom'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    required: bool = False
    custom_validator: Optional[str] = None

# Validation Rules for AM Data
VALIDATION_RULES = {
    "process_parameters": {
        "layer_height": ValidationRule(
            field="layer_height",
            rule_type="range",
            min_value=0.05,
            max_value=0.5,
            required=False
        ),
        "print_speed": ValidationRule(
            field="print_speed",
            rule_type="range",
            min_value=10.0,
            max_value=300.0,
            required=False
        ),
        "nozzle_temperature": ValidationRule(
            field="nozzle_temperature",
            rule_type="range",
            min_value=150.0,
            max_value=350.0,
            required=False
        ),
        "bed_temperature": ValidationRule(
            field="bed_temperature",
            rule_type="range",
            min_value=0.0,
            max_value=150.0,
            required=False
        ),
        "infill_percentage": ValidationRule(
            field="infill_percentage",
            rule_type="range",
            min_value=0.0,
            max_value=100.0,
            required=False
        ),
    },
    "quality_metrics": {
        "tensile_strength_mpa": ValidationRule(
            field="tensile_strength_mpa",
            rule_type="range",
            min_value=0.0,
            max_value=500.0,
            required=False
        ),
        "surface_roughness_um": ValidationRule(
            field="surface_roughness_um",
            rule_type="range",
            min_value=0.0,
            max_value=100.0,
            required=False
        ),
        "porosity_percent": ValidationRule(
            field="porosity_percent",
            rule_type="range",
            min_value=0.0,
            max_value=100.0,
            required=False
        ),
        "density_g_per_cm3": ValidationRule(
            field="density_g_per_cm3",
            rule_type="range",
            min_value=0.5,
            max_value=3.0,
            required=False
        ),
    },
    "geometry_data": {
        "volume_mm3": ValidationRule(
            field="volume_mm3",
            rule_type="range",
            min_value=0.0,
            required=False
        ),
        "surface_area_mm2": ValidationRule(
            field="surface_area_mm2",
            rule_type="range",
            min_value=0.0,
            required=False
        ),
    }
}

class DataQualityPipeline:
    """Main data quality pipeline"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.issues = []
        self.statistics = {}
    
    def validate_experiment(self, experiment_data: Dict[str, Any]) -> List[DataQualityIssue]:
        """Validate a single experiment"""
        issues = []
        
        # Validate process parameters
        if "process_parameters" in experiment_data:
            issues.extend(self._validate_section(
                experiment_data["process_parameters"],
                VALIDATION_RULES["process_parameters"],
                "process_parameters"
            ))
        
        # Validate quality metrics
        if "quality_metrics" in experiment_data:
            issues.extend(self._validate_section(
                experiment_data["quality_metrics"],
                VALIDATION_RULES["quality_metrics"],
                "quality_metrics"
            ))
        
        # Validate geometry data
        if "geometry_data" in experiment_data:
            issues.extend(self._validate_section(
                experiment_data["geometry_data"],
                VALIDATION_RULES["geometry_data"],
                "geometry_data"
            ))
        
        # Cross-field validation
        issues.extend(self._cross_field_validation(experiment_data))
        
        return issues
    
    def _validate_section(self, data: Dict, rules: Dict[str, ValidationRule], section: str) -> List[DataQualityIssue]:
        """Validate a section of data"""
        issues = []
        
        for field, rule in rules.items():
            value = data.get(field)
            
            # Check required fields
            if rule.required and value is None:
                issues.append(DataQualityIssue(
                    issue_type="missing_required",
                    field=f"{section}.{field}",
                    severity="error",
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Provide a value for {field}"
                ))
                continue
            
            if value is None:
                continue  # Skip validation for None values
            
            # Type validation
            if rule.rule_type == "range":
                if isinstance(value, (int, float)):
                    if rule.min_value is not None and value < rule.min_value:
                        issues.append(DataQualityIssue(
                            issue_type="out_of_range",
                            field=f"{section}.{field}",
                            severity="error" if self.validation_level == ValidationLevel.STRICT else "warning",
                            message=f"Value {value} is below minimum {rule.min_value}",
                            value=value,
                            expected_range={"min": rule.min_value, "max": rule.max_value}, # type: ignore
                            suggestion=f"Value should be between {rule.min_value} and {rule.max_value}"
                        ))
                    if rule.max_value is not None and value > rule.max_value:
                        issues.append(DataQualityIssue(
                            issue_type="out_of_range",
                            field=f"{section}.{field}",
                            severity="error" if self.validation_level == ValidationLevel.STRICT else "warning",
                            message=f"Value {value} is above maximum {rule.max_value}",
                            value=value,
                            expected_range={"min": rule.min_value, "max": rule.max_value}, # type: ignore
                            suggestion=f"Value should be between {rule.min_value} and {rule.max_value}"
                        ))
            
            elif rule.rule_type == "allowed_values":
                if rule.allowed_values and value not in rule.allowed_values:
                    issues.append(DataQualityIssue(
                        issue_type="invalid_value",
                        field=f"{section}.{field}",
                        severity="error",
                        message=f"Value {value} is not in allowed values",
                        value=value,
                        suggestion=f"Use one of: {', '.join(map(str, rule.allowed_values))}"
                    ))
        
        return issues
    
    def _cross_field_validation(self, data: Dict) -> List[DataQualityIssue]:
        """Cross-field validation rules"""
        issues = []
        
        # Temperature validation
        if "process_parameters" in data:
            pp = data["process_parameters"]
            nozzle_temp = pp.get("nozzle_temperature")
            bed_temp = pp.get("bed_temperature")
            
            if nozzle_temp and bed_temp:
                if nozzle_temp < bed_temp:
                    issues.append(DataQualityIssue(
                        issue_type="logical_error",
                        field="process_parameters.temperature_relationship",
                        severity="warning",
                        message=f"Nozzle temperature ({nozzle_temp}°C) is lower than bed temperature ({bed_temp}°C)",
                        suggestion="Verify temperature settings"
                    ))
        
        # Geometry consistency
        if "geometry_data" in data:
            gd = data["geometry_data"]
            volume = gd.get("volume_mm3")
            bbox_x = gd.get("bounding_box_x")
            bbox_y = gd.get("bounding_box_y")
            bbox_z = gd.get("bounding_box_z")
            
            if volume and bbox_x and bbox_y and bbox_z:
                estimated_volume = bbox_x * bbox_y * bbox_z
                if volume > estimated_volume * 1.5:  # Allow 50% tolerance
                    issues.append(DataQualityIssue(
                        issue_type="consistency_warning",
                        field="geometry_data.volume",
                        severity="warning",
                        message=f"Volume ({volume}) seems inconsistent with bounding box dimensions",
                        suggestion="Verify geometry measurements"
                    ))
        
        return issues
    
    def detect_outliers(self, data: pd.DataFrame, columns: List[str], method: str = "iqr") -> pd.DataFrame:
        """Detect outliers using IQR or Z-score method"""
        outliers_mask = pd.Series([False] * len(data))
        
        for col in columns:
            if col not in data.columns:
                continue
            
            values = data[col].dropna()
            if len(values) < 3:
                continue
            
            if method == "iqr":
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                col_outliers = (data[col] < lower_bound) | (data[col] > upper_bound)
            
            elif method == "zscore":
                z_scores = np.abs(stats.zscore(values))
                threshold = 3
                col_outliers = pd.Series([False] * len(data))
                col_outliers[values.index] = z_scores > threshold
            
            outliers_mask = outliers_mask | col_outliers # type: ignore
        
        return data[outliers_mask]
    
    def handle_missing_values(
        self,
        data: pd.DataFrame,
        strategy: str = "mean",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Handle missing values"""
        data_cleaned = data.copy()
        
        if columns is None:
            columns = data.columns.tolist()
        
        numeric_columns = data[columns].select_dtypes(include=[np.number]).columns.tolist()
        
        if strategy == "mean":
            imputer = SimpleImputer(strategy="mean")
        elif strategy == "median":
            imputer = SimpleImputer(strategy="median")
        elif strategy == "mode":
            imputer = SimpleImputer(strategy="most_frequent")
        elif strategy == "knn":
            imputer = KNNImputer(n_neighbors=5)
        else:
            imputer = SimpleImputer(strategy="constant", fill_value=0)
        
        if numeric_columns:
            data_cleaned[numeric_columns] = imputer.fit_transform(data[numeric_columns])
        
        return data_cleaned
    
    def remove_duplicates(self, data: pd.DataFrame, subset: Optional[List[str]] = None) -> Tuple[pd.DataFrame, int]:
        """Remove duplicate records"""
        initial_count = len(data)
        data_cleaned = data.drop_duplicates(subset=subset, keep="first")
        removed_count = initial_count - len(data_cleaned)
        return data_cleaned, removed_count
    
    def normalize_data(
        self,
        data: pd.DataFrame,
        columns: List[str],
        method: str = "standard"
    ) -> pd.DataFrame:
        """Normalize data"""
        data_normalized = data.copy()
        
        numeric_cols = [col for col in columns if col in data.columns and data[col].dtype in [np.float64, np.int64]]
        
        if not numeric_cols:
            return data_normalized
        
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        elif method == "robust":
            scaler = RobustScaler()
        else:
            return data_normalized
        
        data_normalized[numeric_cols] = scaler.fit_transform(data[numeric_cols])
        
        return data_normalized
    
    def generate_quality_report(
        self,
        experiments: List[Dict[str, Any]],
        experiment_id: Optional[str] = None
    ) -> DataQualityReport:
        """Generate comprehensive quality report"""
        issues = []
        total_records = len(experiments)
        valid_records = 0
        
        # Validate each experiment
        for exp in experiments:
            exp_issues = self.validate_experiment(exp)
            issues.extend(exp_issues)
            if not exp_issues:
                valid_records += 1
        
        # Calculate scores
        completeness_score = self._calculate_completeness(experiments)
        validity_score = valid_records / total_records if total_records > 0 else 0
        consistency_score = self._calculate_consistency(experiments)
        overall_score = (completeness_score + validity_score + consistency_score) / 3
        
        # Generate statistics
        statistics = self._generate_statistics(experiments)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, statistics)
        
        return DataQualityReport(
            experiment_id=experiment_id or "batch",
            timestamp=datetime.now(),
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=total_records - valid_records,
            completeness_score=completeness_score,
            validity_score=validity_score,
            consistency_score=consistency_score,
            overall_score=overall_score,
            issues=issues,
            statistics=statistics,
            recommendations=recommendations
        )
    
    def _calculate_completeness(self, experiments: List[Dict]) -> float:
        """Calculate data completeness score"""
        if not experiments:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for exp in experiments:
            for section in ["process_parameters", "quality_metrics", "geometry_data"]:
                if section in exp:
                    section_data = exp[section]
                    for key, value in section_data.items():
                        total_fields += 1
                        if value is not None:
                            filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_consistency(self, experiments: List[Dict]) -> float:
        """Calculate data consistency score"""
        if len(experiments) < 2:
            return 1.0
        
        # Check for consistent patterns
        consistency_checks = 0
        consistent_checks = 0
        
        # Check temperature consistency
        for exp in experiments:
            if "process_parameters" in exp:
                pp = exp["process_parameters"]
                nozzle_temp = pp.get("nozzle_temperature")
                bed_temp = pp.get("bed_temperature")
                if nozzle_temp and bed_temp:
                    consistency_checks += 1
                    if nozzle_temp > bed_temp:
                        consistent_checks += 1
        
        return consistent_checks / consistency_checks if consistency_checks > 0 else 1.0
    
    def _generate_statistics(self, experiments: List[Dict]) -> Dict[str, Any]:
        """Generate statistical summary"""
        stats = {
            "total_experiments": len(experiments),
            "fields_with_data": {},
            "missing_fields": {},
            "outlier_counts": {}
        }
        
        # Collect field statistics
        for exp in experiments:
            for section in ["process_parameters", "quality_metrics", "geometry_data"]:
                if section in exp:
                    for key, value in exp[section].items():
                        field_key = f"{section}.{key}"
                        if value is not None:
                            stats["fields_with_data"][field_key] = stats["fields_with_data"].get(field_key, 0) + 1
                        else:
                            stats["missing_fields"][field_key] = stats["missing_fields"].get(field_key, 0) + 1
        
        return stats
    
    def _generate_recommendations(self, issues: List[DataQualityIssue], statistics: Dict) -> List[str]:
        """Generate recommendations based on issues"""
        recommendations = []
        
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        
        if error_count > 0:
            recommendations.append(f"Fix {error_count} critical errors before proceeding")
        
        if warning_count > 10:
            recommendations.append("Review and address multiple warnings")
        
        missing_fields = statistics.get("missing_fields", {})
        if missing_fields:
            top_missing = sorted(missing_fields.items(), key=lambda x: x[1], reverse=True)[:3]
            recommendations.append(f"Consider filling missing fields: {', '.join([f[0] for f in top_missing])}")
        
        return recommendations
    
    def clean_dataset(
        self,
        data: pd.DataFrame,
        remove_outliers: bool = True,
        handle_missing: bool = True,
        remove_duplicates: bool = True,
        normalize: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Complete data cleaning pipeline"""
        cleaning_log = {
            "initial_rows": len(data),
            "steps": []
        }
        
        data_cleaned = data.copy()
        
        # Remove duplicates
        if remove_duplicates:
            data_cleaned, dup_count = self.remove_duplicates(data_cleaned)
            cleaning_log["steps"].append({
                "step": "remove_duplicates",
                "removed": dup_count
            })
        
        # Handle missing values
        if handle_missing:
            missing_before = data_cleaned.isnull().sum().sum()
            data_cleaned = self.handle_missing_values(data_cleaned, strategy="mean")
            missing_after = data_cleaned.isnull().sum().sum()
            cleaning_log["steps"].append({
                "step": "handle_missing",
                "filled": missing_before - missing_after
            })
        
        # Remove outliers
        if remove_outliers:
            numeric_cols = data_cleaned.select_dtypes(include=[np.number]).columns.tolist()
            outliers = self.detect_outliers(data_cleaned, numeric_cols)
            outlier_count = len(outliers)
            data_cleaned = data_cleaned[~data_cleaned.index.isin(outliers.index)]
            cleaning_log["steps"].append({
                "step": "remove_outliers",
                "removed": outlier_count
            })
        
        # Normalize
        if normalize:
            numeric_cols = data_cleaned.select_dtypes(include=[np.number]).columns.tolist()
            data_cleaned = self.normalize_data(data_cleaned, numeric_cols, method="standard")
            cleaning_log["steps"].append({
                "step": "normalize",
                "normalized_columns": len(numeric_cols)
            })
        
        cleaning_log["final_rows"] = len(data_cleaned)
        cleaning_log["rows_removed"] = cleaning_log["initial_rows"] - cleaning_log["final_rows"]
        
        return data_cleaned, cleaning_log
