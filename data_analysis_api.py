"""
Data Analysis and Visualization API
RESTful API endpoints for data exploration and analysis
"""

from fastapi import FastAPI, HTTPException, Query, Path, Depends, Body, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

# Import analysis and visualization modules
from data_analysis_pipeline import DataAnalysisPipeline, AnalysisReport
from visualization_generator import VisualizationGenerator

# Import database
from am_data_pipeline_postgres import get_db, Experiment

# Import existing API
from restful_api import app

# Pydantic Models
class AnalysisRequestModel(BaseModel):
    experiment_ids: Optional[List[str]] = None
    material_type: Optional[str] = None
    include_visualizations: bool = True

class VisualizationRequestModel(BaseModel):
    plot_type: str = Field(..., description="Type of plot: scatter, heatmap, distribution, time_series, pair_plot, cluster, pca, dashboard")
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_by: Optional[str] = None
    columns: Optional[List[str]] = None
    title: Optional[str] = None

# API Endpoints

@app.post(
    "/api/v1/analysis/explore",
    tags=["Data Analysis"],
    summary="Exploratory Data Analysis",
    description="Perform comprehensive exploratory data analysis"
)
def explore_data(
    request: AnalysisRequestModel = ..., # type: ignore
    db: Session = Depends(get_db)
):
    """Perform exploratory data analysis"""
    try:
        # Get experiments
        query = db.query(Experiment)
        
        if request.experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(request.experiment_ids))
        if request.material_type:
            query = query.filter(Experiment.material_type == request.material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        exp_ids = []
        for exp in experiments:
            exp_ids.append(exp.experiment_id)
            row = {"experiment_id": exp.experiment_id}
            
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                    "density_g_per_cm3": exp.quality_metrics.density_g_per_cm3,
                })
            
            if exp.geometry_data:
                row.update({
                    "volume_mm3": exp.geometry_data.volume_mm3,
                    "surface_area_mm2": exp.geometry_data.surface_area_mm2,
                })
            
            if exp.build_date: # type: ignore
                row["build_date"] = exp.build_date # type: ignore
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Perform analysis
        pipeline = DataAnalysisPipeline()
        report = pipeline.generate_analysis_report(df, exp_ids)
        
        result = {
            "report": report.dict(),
            "data_summary": {
                "total_experiments": len(experiments),
                "columns": df.columns.tolist(),
                "shape": list(df.shape)
            }
        }
        
        # Add visualizations if requested
        if request.include_visualizations:
            viz_gen = VisualizationGenerator()
            
            # Correlation heatmap
            try:
                heatmap = viz_gen.create_correlation_heatmap(df)
                result["visualizations"] = {"correlation_heatmap": heatmap}
            except:
                pass
            
            # Summary dashboard
            try:
                dashboard = viz_gen.create_summary_dashboard(df)
                result["visualizations"]["summary_dashboard"] = dashboard
            except:
                pass
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )

@app.post(
    "/api/v1/analysis/visualize",
    tags=["Data Analysis"],
    summary="Create visualization",
    description="Generate specific visualization"
)
def create_visualization(
    request: VisualizationRequestModel = ..., # type: ignore
    experiment_ids: Optional[List[str]] = Body(None),
    material_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Create visualization"""
    try:
        # Get experiments (similar to explore endpoint)
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {"experiment_id": exp.experiment_id}
            
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            
            if exp.build_date: # type: ignore
                row["build_date"] = exp.build_date # type: ignore
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Generate visualization
        viz_gen = VisualizationGenerator()
        
        if request.plot_type == "scatter":
            if not request.x_column or not request.y_column:
                raise HTTPException(status_code=400, detail="x_column and y_column required for scatter plot")
            viz = viz_gen.create_scatter_plot(
                df, request.x_column, request.y_column,
                request.color_by, request.title
            )
        
        elif request.plot_type == "heatmap":
            viz = viz_gen.create_correlation_heatmap(df, request.title)
        
        elif request.plot_type == "distribution":
            if not request.x_column:
                raise HTTPException(status_code=400, detail="x_column required for distribution plot")
            viz = viz_gen.create_distribution_plot(df, request.x_column, "histogram")
        
        elif request.plot_type == "time_series":
            if not request.x_column or not request.y_column:
                raise HTTPException(status_code=400, detail="x_column and y_column required for time series")
            viz = viz_gen.create_time_series_plot(
                df, request.x_column, request.y_column, request.title
            )
        
        elif request.plot_type == "pair_plot":
            viz = viz_gen.create_pair_plot(df, request.columns)
        
        elif request.plot_type == "dashboard":
            viz = viz_gen.create_summary_dashboard(df, request.title)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown plot type: {request.plot_type}")
        
        return viz
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization error: {str(e)}"
        )

@app.get(
    "/api/v1/analysis/statistics",
    tags=["Data Analysis"],
    summary="Get statistical summary",
    description="Get statistical summary for experiments"
)
def get_statistics(
    experiment_ids: Optional[List[str]] = Query(None),
    material_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistical summary"""
    try:
        # Get experiments and convert to DataFrame (similar to above)
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {}
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Generate statistics
        pipeline = DataAnalysisPipeline()
        stats_summary = pipeline.generate_statistical_summary(df)
        
        return {
            "statistics": {k: v.dict() for k, v in stats_summary.items()},
            "total_experiments": len(experiments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@app.get(
    "/api/v1/analysis/correlations",
    tags=["Data Analysis"],
    summary="Get correlation analysis",
    description="Analyze correlations between variables"
)
def get_correlations(
    experiment_ids: Optional[List[str]] = Query(None),
    material_type: Optional[str] = Query(None),
    threshold: float = Query(0.7, ge=0, le=1),
    db: Session = Depends(get_db)
):
    """Get correlation analysis"""
    try:
        # Get experiments and convert to DataFrame (similar to above)
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {}
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Analyze correlations
        pipeline = DataAnalysisPipeline()
        corr_analysis = pipeline.analyze_correlations(df, threshold=threshold)
        
        return corr_analysis.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@app.post(
    "/api/v1/analysis/pca",
    tags=["Data Analysis"],
    summary="Perform PCA",
    description="Perform Principal Component Analysis"
)
def perform_pca(
    experiment_ids: Optional[List[str]] = Body(None),
    material_type: Optional[str] = Query(None),
    n_components: int = Query(2, ge=2, le=10),
    db: Session = Depends(get_db)
):
    """Perform PCA"""
    try:
        # Get experiments and convert to DataFrame
        query = db.query(Experiment)
        
        if experiment_ids:
            query = query.filter(Experiment.experiment_id.in_(experiment_ids))
        if material_type:
            query = query.filter(Experiment.material_type == material_type)
        
        experiments = query.all()
        
        if not experiments:
            raise HTTPException(status_code=404, detail="No experiments found")
        
        # Convert to DataFrame
        data_rows = []
        for exp in experiments:
            row = {}
            if exp.process_parameters:
                row.update({
                    "layer_height": exp.process_parameters.layer_height,
                    "print_speed": exp.process_parameters.print_speed,
                    "nozzle_temperature": exp.process_parameters.nozzle_temperature,
                    "bed_temperature": exp.process_parameters.bed_temperature,
                    "infill_percentage": exp.process_parameters.infill_percentage,
                })
            if exp.quality_metrics:
                row.update({
                    "tensile_strength_mpa": exp.quality_metrics.tensile_strength_mpa,
                    "surface_roughness_um": exp.quality_metrics.surface_roughness_um,
                    "porosity_percent": exp.quality_metrics.porosity_percent,
                })
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Perform PCA
        pipeline = DataAnalysisPipeline()
        pca_result = pipeline.perform_pca(df, n_components=n_components)
        
        # Generate visualization
        if "error" not in pca_result:
            viz_gen = VisualizationGenerator()
            viz = viz_gen.create_pca_visualization(pca_result)
            pca_result["visualization"] = viz
        
        return pca_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
