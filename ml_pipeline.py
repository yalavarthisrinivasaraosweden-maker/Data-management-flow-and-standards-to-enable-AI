"""
Data modeling and machine learning pipeline for prediction and forecasting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class TrainingResult:
    model_name: str
    target: str
    features: List[str]
    metrics: Dict[str, float]
    model_path: str


class MLPipeline:
    """Train, persist, and use ML models for AM data."""

    def __init__(self, model_dir: str = "ml_models") -> None:
        self.model_dir = model_dir

    def _split_columns(self, df: pd.DataFrame, features: List[str]) -> Tuple[List[str], List[str]]:
        numeric_features = []
        categorical_features = []
        for col in features:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_features.append(col)
            else:
                categorical_features.append(col)
        return numeric_features, categorical_features

    def _build_preprocessor(self, df: pd.DataFrame, features: List[str]) -> ColumnTransformer:
        num_cols, cat_cols = self._split_columns(df, features)

        numeric_pipe = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical_pipe = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]
        )

        return ColumnTransformer(
            transformers=[
                ("num", numeric_pipe, num_cols),
                ("cat", categorical_pipe, cat_cols),
            ],
            remainder="drop",
        )

    def train_regression(
        self,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: List[str],
        model_type: str = "random_forest",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> TrainingResult:
        if target_col not in df.columns:
            raise ValueError(f"Target '{target_col}' not found")
        for col in feature_cols:
            if col not in df.columns:
                raise ValueError(f"Feature '{col}' not found")

        train_df = df[feature_cols + [target_col]].dropna(subset=[target_col])
        if len(train_df) < 10:
            raise ValueError("Not enough rows to train model (need at least 10)")

        X = train_df[feature_cols]
        y = train_df[target_col].astype(float)

        preprocessor = self._build_preprocessor(train_df, feature_cols)
        if model_type == "linear":
            estimator = LinearRegression()
            model_name = "linear_regression"
        else:
            estimator = RandomForestRegressor(
                n_estimators=300,
                random_state=random_state,
                max_depth=None,
                min_samples_split=2,
            )
            model_name = "random_forest_regressor"

        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", estimator),
            ]
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        metrics = {
            "r2": float(r2_score(y_test, preds)),
            "mae": float(mean_absolute_error(y_test, preds)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
            "train_rows": float(len(X_train)),
            "test_rows": float(len(X_test)),
        }

        import os
        os.makedirs(self.model_dir, exist_ok=True)
        model_path = os.path.join(self.model_dir, f"{target_col}_{model_name}.joblib")
        joblib.dump(
            {
                "pipeline": pipeline,
                "target": target_col,
                "features": feature_cols,
                "model_name": model_name,
                "metrics": metrics,
            },
            model_path,
        )

        return TrainingResult(
            model_name=model_name,
            target=target_col,
            features=feature_cols,
            metrics=metrics,
            model_path=model_path,
        )

    def predict(self, model_path: str, records: List[Dict[str, Any]]) -> List[float]:
        bundle = joblib.load(model_path)
        pipeline: Pipeline = bundle["pipeline"]
        feature_cols: List[str] = bundle["features"]
        df = pd.DataFrame(records)
        # Ensure all expected features exist
        for col in feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        preds = pipeline.predict(df[feature_cols])
        return [float(p) for p in preds]

    def forecast_linear(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        periods: int = 10,
    ) -> Dict[str, Any]:
        if date_col not in df.columns or value_col not in df.columns:
            raise ValueError("date_col or value_col not found")

        series_df = df[[date_col, value_col]].dropna().copy()
        if len(series_df) < 5:
            raise ValueError("Need at least 5 points for forecasting")

        series_df[date_col] = pd.to_datetime(series_df[date_col], errors="coerce")
        series_df = series_df.dropna(subset=[date_col]).sort_values(date_col)
        series_df["t"] = np.arange(len(series_df))

        model = LinearRegression()
        model.fit(series_df[["t"]], series_df[value_col].astype(float))

        future_idx = np.arange(len(series_df), len(series_df) + periods)
        future_vals = model.predict(future_idx.reshape(-1, 1))

        last_date = series_df[date_col].iloc[-1]
        inferred_freq = pd.infer_freq(series_df[date_col]) or "D"
        future_dates = pd.date_range(start=last_date, periods=periods + 1, freq=inferred_freq)[1:]

        return {
            "history": [
                {"date": d.isoformat(), "value": float(v)}
                for d, v in zip(series_df[date_col], series_df[value_col])
            ],
            "forecast": [
                {"date": d.isoformat(), "value": float(v)}
                for d, v in zip(future_dates, future_vals)
            ],
            "slope": float(model.coef_[0]),
            "intercept": float(model.intercept_),
        }
