"""
IEQ Analytics Module

This module provides comprehensive Indoor Environmental Quality (IEQ) analysis capabilities,
including statistical analysis, comfort assessment based on EN16798-1 2019, and rule-based evaluation based on user-defined rules.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import warnings

from .models import Room, Building, IEQData
from .enums import IEQParameter, ComfortCategory
from .utils import sanitize_correlation_value, sanitize_correlation_matrix
from .rule_builder import AnalyticsEngine


class IEQAnalytics:
    """Main analytics engine for IEQ data analysis."""
    
    def __init__(self, rules_config_path: Optional[Path] = None):
        """Initialize analytics engine."""
        config = self._load_comfort_thresholds()
        self.comfort_thresholds = config.get("comfort_thresholds", {})
        self.room_types = config.get("room_types", {})
        
        # Initialize rule-based analytics engine
        if rules_config_path is None:
            rules_config_path = Path(__file__).parent.parent / "config" / "analytics_rules.yaml"
        
        self.rules_engine = None
        if rules_config_path and rules_config_path.exists():
            try:
                self.rules_engine = AnalyticsEngine(rules_config_path)
            except Exception as e:
                print(f"Warning: Could not load rules engine: {e}")
                self.rules_engine = None
        
    def _load_comfort_thresholds(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load comfort thresholds and room types from EN 16798-1 config file."""
        import yaml
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "en16798_thresholds.yaml"
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            # Map category keys to enum values for internal use
            thresholds = config.get("comfort_thresholds", {})
            for param, categories in thresholds.items():
                for cat in list(categories.keys()):
                    if hasattr(ComfortCategory, cat):
                        categories[getattr(ComfortCategory, cat).value] = categories.pop(cat)
            config["comfort_thresholds"] = thresholds
            return config
        except Exception as e:
            print(f"Warning: Could not load EN 16798-1 config: {e}")
            # Fallback to hardcoded values if config fails
            return {
                "comfort_thresholds": {
                    "temperature": {
                        ComfortCategory.CATEGORY_I.value: {"min": 21.0, "max": 23.0},
                        ComfortCategory.CATEGORY_II.value: {"min": 20.0, "max": 24.0},
                        ComfortCategory.CATEGORY_III.value: {"min": 19.0, "max": 25.0},
                    },
                    "humidity": {
                        ComfortCategory.CATEGORY_I.value: {"min": 30.0, "max": 50.0},
                        ComfortCategory.CATEGORY_II.value: {"min": 25.0, "max": 60.0},
                        ComfortCategory.CATEGORY_III.value: {"min": 20.0, "max": 70.0},
                    },
                    "co2": {
                        ComfortCategory.CATEGORY_I.value: {"max": 550.0},
                        ComfortCategory.CATEGORY_II.value: {"max": 800.0},
                        ComfortCategory.CATEGORY_III.value: {"max": 1200.0},
                    }
                },
                "room_types": {}
            }
    
    def analyze_room_data(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Comprehensive analysis of a single room's IEQ data."""
        
        analysis_results = {
            "room_id": ieq_data.room_id,
            "building_id": ieq_data.building_id,
            "data_period": {
                "start": ieq_data.data_period_start.isoformat() if ieq_data.data_period_start else None,
                "end": ieq_data.data_period_end.isoformat() if ieq_data.data_period_end else None,
                "duration_days": None
            },
            "data_quality": self._analyze_data_quality(ieq_data),
            "basic_statistics": self._calculate_basic_statistics(ieq_data),
            "comfort_analysis": self._analyze_comfort_compliance(ieq_data),
            "temporal_patterns": self._analyze_temporal_patterns(ieq_data),
            "correlation_analysis": self._analyze_correlations(ieq_data),
            "outlier_detection": self._detect_outliers(ieq_data),
            "recommendations": []
        }
        
        # Calculate duration
        if ieq_data.data_period_start and ieq_data.data_period_end:
            duration = ieq_data.data_period_end - ieq_data.data_period_start
            analysis_results["data_period"]["duration_days"] = duration.days
        
        # Generate recommendations
        analysis_results["recommendations"] = self._generate_recommendations(analysis_results)
        
        # Add rule-based analysis if available
        if self.rules_engine:
            try:
                analysis_results["rule_based_analysis"] = self._analyze_with_rules(ieq_data)
                analysis_results["en_standard_analysis"] = self._analyze_en_standard(ieq_data)
            except Exception as e:
                analysis_results["rule_based_analysis"] = {"error": f"Rule analysis failed: {e}"}
                analysis_results["en_standard_analysis"] = {"error": f"EN standard analysis failed: {e}"}

        # --- ACH metrics integration ---
        try:
            from .ventilation_rate_predictor import VentilationRatePredictor
            co2_col = None
            for col in ieq_data.data.columns:
                if "co2" in col.lower():
                    co2_col = col
                    break
            ach_metrics = {}
            if co2_col:
                predictor = VentilationRatePredictor(co2_col=co2_col)
                ach_results = predictor.analyze(ieq_data.data)
                # Use summarize_ach_statistics logic to compute metrics
                ach_values = []
                weights = []
                for r in ach_results:
                    ach = r.get('ventilation_rate_ach')
                    n_points = len(r.get('values', []))
                    if ach is not None and n_points > 1:
                        ach_values.append(ach)
                        weights.append(n_points)
                if ach_values:
                    ach_mean = float(np.average(ach_values, weights=weights))
                    ach_median = float(np.median(ach_values))
                    ach_std = float(np.sqrt(np.average((np.array(ach_values)-ach_mean)**2, weights=weights)))
                    ach_min = float(np.min(ach_values))
                    ach_max = float(np.max(ach_values))
                    n_periods = len(ach_values)
                    total_points = sum(weights)
                    p_periods = min(n_periods / 20, 1.0)
                    p_points = min(total_points / 100, 1.0)
                    p_std = max(0, 1 - ach_std / 0.05)
                    confidence_prob = round((0.4*p_periods + 0.4*p_points + 0.2*p_std), 2)
                    if confidence_prob > 0.85:
                        confidence = "High"
                    elif confidence_prob > 0.6:
                        confidence = "Medium"
                    else:
                        confidence = "Low"
                    recommended_ach = 2.0
                    ventilation_status = (
                        f"Well ventilated (mean ACH {ach_mean:.2f} ≥ recommended {recommended_ach})"
                        if ach_mean >= recommended_ach else
                        f"Poorly ventilated (mean ACH {ach_mean:.2f} < recommended {recommended_ach})"
                    )
                    ach_metrics = {
                        "ach_mean": ach_mean,
                        "ach_median": ach_median,
                        "ach_std": ach_std,
                        "ach_min": ach_min,
                        "ach_max": ach_max,
                        "n_periods": n_periods,
                        "total_points": total_points,
                        "confidence": confidence,
                        "confidence_prob": confidence_prob,
                        "ventilation_status": ventilation_status
                    }
            analysis_results["ach_metrics"] = ach_metrics
        except Exception as e:
            analysis_results["ach_metrics"] = {"error": f"ACH calculation failed: {e}"}

        return analysis_results
    
    def _analyze_data_quality(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze data quality metrics."""
        data = ieq_data.data
        
        quality_metrics = {
            "total_records": len(data),
            "completeness": {},
            "missing_data_periods": [],
            "duplicate_timestamps": 0,
            "overall_score": 0.0
        }
        
        # Calculate completeness for each column
        for col in data.columns:
            non_null_count = data[col].count()
            completeness = non_null_count / len(data) if len(data) > 0 else 0
            quality_metrics["completeness"][col] = {
                "percentage": round(completeness * 100, 2),
                "missing_count": len(data) - non_null_count,
                "non_null_count": non_null_count
            }
        
        # Detect missing data periods
        if len(data) > 1:
            expected_freq = pd.Timedelta(hours=1)
            time_diffs = data.index[1:] - data.index[:-1]
            
            # Find large gaps (more than 1.5 times expected frequency)
            for i, time_diff in enumerate(time_diffs):
                if time_diff > expected_freq * 1.5:
                    # The gap starts at index i (before the large time difference)
                    gap_start = data.index[i]
                    quality_metrics["missing_data_periods"].append({
                        "start": gap_start.isoformat(),
                        "duration_hours": time_diff.total_seconds() / 3600
                    })
        
        # Check for duplicate timestamps
        quality_metrics["duplicate_timestamps"] = data.index.duplicated().sum()
        
        # Calculate overall quality score
        avg_completeness = np.mean([m["percentage"] for m in quality_metrics["completeness"].values()])
        gap_penalty = len(quality_metrics["missing_data_periods"]) * 5
        duplicate_penalty = quality_metrics["duplicate_timestamps"] * 2
        
        quality_metrics["overall_score"] = max(0, avg_completeness - gap_penalty - duplicate_penalty) / 100
        
        return quality_metrics
    
    def _calculate_basic_statistics(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Calculate basic statistical measures."""
        data = ieq_data.data
        stats = {}
        
        measurement_columns = [col for col in data.columns 
                             if any(param.value in col.lower() 
                                   for param in IEQParameter.get_measurement_parameters())]
        
        for col in measurement_columns:
            if data[col].dtype in ['int64', 'float64'] and data[col].count() > 0:
                series_data = data[col].dropna()
                
                stats[col] = {
                    "mean": round(series_data.mean(), 2),
                    "median": round(series_data.median(), 2),
                    "std": round(series_data.std(), 2),
                    "min": round(series_data.min(), 2),
                    "max": round(series_data.max(), 2),
                    "q25": round(series_data.quantile(0.25), 2),
                    "q75": round(series_data.quantile(0.75), 2),
                    "range": round(series_data.max() - series_data.min(), 2)
                }
        
        return stats
    
    def _analyze_comfort_compliance(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze compliance with comfort standards."""
        data = ieq_data.data
        compliance_results = {}
        
        # Map data columns to standard parameters
        param_mapping = {
            "temperature": [col for col in data.columns if "temperature" in col.lower() or "temp" in col.lower()],
            "humidity": [col for col in data.columns if "humidity" in col.lower() or "fugtighed" in col.lower()],
            "co2": [col for col in data.columns if "co2" in col.lower()]
        }
        
        for param, columns in param_mapping.items():
            if not columns or param not in self.comfort_thresholds:
                continue
                
            # Use the first matching column
            col = columns[0]
            if col not in data.columns or data[col].count() == 0:
                continue
            
            # Drop NA and keep index for alignment
            valid_series = data[col].dropna()
            thresholds = self.comfort_thresholds[param]
            compliance_results[param] = {}
            for category, limits in thresholds.items():
                if param == "co2":
                    # CO2 only has upper limit
                    compliant = valid_series <= limits["max"]
                else:
                    # Temperature and humidity have ranges
                    compliant = (valid_series >= limits["min"]) & (valid_series <= limits["max"])
                # compliant and valid_series are already aligned - no need to reindex
                compliance_percentage = (compliant.sum() / len(valid_series)) * 100
                compliance_results[param][category] = {
                    "compliance_percentage": round(compliance_percentage, 2),
                    "compliant_hours": int(compliant.sum()),
                    "total_hours": int(len(valid_series)),
                    "thresholds": limits
                }
        
        return compliance_results
    
    def _analyze_temporal_patterns(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze temporal patterns in the data."""
        data = ieq_data.data.copy()
        
        # Ensure index is a DatetimeIndex
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # Add time-based features
        data['hour'] = data.index.hour
        data['day_of_week'] = data.index.dayofweek
        data['month'] = data.index.month
        data['is_weekend'] = data.index.dayofweek >= 5
        
        patterns = {}
        
        measurement_columns = [col for col in data.columns 
                             if any(param.value in col.lower() 
                                   for param in IEQParameter.get_measurement_parameters())]
        
        for col in measurement_columns:
            if data[col].dtype in ['int64', 'float64'] and data[col].count() > 0:
                patterns[col] = {
                    "hourly_averages": data.groupby('hour')[col].mean().round(2).to_dict(),
                    "daily_averages": data.groupby('day_of_week')[col].mean().round(2).to_dict(),
                    "monthly_averages": data.groupby('month')[col].mean().round(2).to_dict(),
                    "weekend_vs_weekday": {
                        "weekday_avg": round(data[~data['is_weekend']][col].mean(), 2),
                        "weekend_avg": round(data[data['is_weekend']][col].mean(), 2)
                    }
                }
        
        return patterns
    
    def _analyze_correlations(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze correlations between IEQ parameters."""
        data = ieq_data.data
        
        measurement_columns = [col for col in data.columns 
                             if any(param.value in col.lower() 
                                   for param in IEQParameter.get_measurement_parameters())]
        
        if len(measurement_columns) < 2:
            return {"correlations": {}, "note": "Insufficient measurement columns for correlation analysis"}
        
        # Calculate correlation matrix
        correlation_data = data[measurement_columns].select_dtypes(include=[np.number])
        
        if correlation_data.empty:
            return {"correlations": {}, "note": "No numeric measurement data available"}
        
        corr_matrix = correlation_data.corr()
        
        # Convert to dictionary format using utility function
        correlations = sanitize_correlation_matrix(corr_matrix)
        
        return {"correlations": correlations}
    
    def _detect_outliers(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Detect outliers using statistical methods."""
        data = ieq_data.data
        outliers = {}
        
        measurement_columns = [col for col in data.columns 
                             if any(param.value in col.lower() 
                                   for param in IEQParameter.get_measurement_parameters())]
        
        for col in measurement_columns:
            if data[col].dtype in ['int64', 'float64'] and data[col].count() > 0:
                series_data = data[col].dropna()
                
                # Using IQR method
                Q1 = series_data.quantile(0.25)
                Q3 = series_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (series_data < lower_bound) | (series_data > upper_bound)
                outlier_count = outlier_mask.sum()
                
                outliers[col] = {
                    "count": outlier_count,
                    "percentage": round((outlier_count / len(series_data)) * 100, 2),
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2),
                    "outlier_values": series_data[outlier_mask].tolist()[:10]  # First 10 outliers
                }
        
        return outliers
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Data quality recommendations
        data_quality = analysis_results.get("data_quality", {})
        overall_score = data_quality.get("overall_score", 0)
        
        if overall_score < 0.8:
            recommendations.append("⚠️ Data quality is below acceptable threshold. Consider sensor maintenance or calibration.")
        
        # Check for missing data
        missing_periods = data_quality.get("missing_data_periods", [])
        if len(missing_periods) > 5:
            recommendations.append("📊 Multiple data gaps detected. Review sensor connectivity and data logging systems.")
        
        # Comfort compliance recommendations
        comfort_analysis = analysis_results.get("comfort_analysis", {})
        
        for param, categories in comfort_analysis.items():
            category_ii = categories.get(ComfortCategory.CATEGORY_II.value, {})
            compliance = category_ii.get("compliance_percentage", 100)
            
            if compliance < 80:
                if param == "temperature":
                    recommendations.append(f"🌡️ Temperature comfort compliance is {compliance:.1f}%. Consider HVAC adjustments.")
                elif param == "humidity":
                    recommendations.append(f"💧 Humidity levels are outside comfort range {compliance:.1f}% of the time. Check ventilation systems.")
                elif param == "co2":
                    recommendations.append(f"🫁 CO2 levels exceed recommendations {100-compliance:.1f}% of the time. Increase ventilation rate.")
        
        # Outlier recommendations
        outliers = analysis_results.get("outlier_detection", {})
        for param, outlier_info in outliers.items():
            if outlier_info.get("percentage", 0) > 5:
                recommendations.append(f"📈 High number of outliers detected in {param} ({outlier_info['percentage']:.1f}%). Investigate sensor accuracy.")
        
        if not recommendations:
            recommendations.append("✅ No major issues detected. IEQ conditions appear to be within acceptable ranges.")
        
        return recommendations
    
    def _analyze_with_rules(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze IEQ data using configured rules."""
        if not self.rules_engine:
            return {"error": "Rules engine not available"}
        
        try:
            return self.rules_engine.analyze_all_rules(ieq_data)
        except Exception as e:
            return {"error": f"Rule analysis failed: {e}"}
    
    def _analyze_en_standard(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze IEQ data against EN 16798-1 standard."""
        if not self.rules_engine:
            return {"error": "Rules engine not available"}
        
        try:
            return self.rules_engine.analyze_en_standard(ieq_data)
        except Exception as e:
            return {"error": f"EN standard analysis failed: {e}"}
    
    def aggregate_building_analysis(self, room_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate room-level analyses to building level."""
        
        if not room_analyses:
            return {"error": "No room analyses provided"}
        
        building_id = room_analyses[0]["building_id"]
        
        building_analysis = {
            "building_id": building_id,
            "room_count": len(room_analyses),
            "rooms": [analysis["room_id"] for analysis in room_analyses],
            "aggregated_statistics": {},
            "building_comfort_summary": {},
            "data_quality_summary": {},
            "building_recommendations": []
        }
        
        # Aggregate basic statistics
        all_stats = {}
        for analysis in room_analyses:
            for param, stats in analysis.get("basic_statistics", {}).items():
                if param not in all_stats:
                    all_stats[param] = []
                all_stats[param].append(stats)
        
        for param, room_stats in all_stats.items():
            means = [s["mean"] for s in room_stats]
            building_analysis["aggregated_statistics"][param] = {
                "building_average": round(np.mean(means), 2),
                "room_variation": round(np.std(means), 2),
                "min_room_avg": round(min(means), 2),
                "max_room_avg": round(max(means), 2)
            }
        
        # Aggregate comfort compliance
        comfort_summary = {}
        for analysis in room_analyses:
            for param, categories in analysis.get("comfort_analysis", {}).items():
                if param not in comfort_summary:
                    comfort_summary[param] = []
                
                category_ii = categories.get(ComfortCategory.CATEGORY_II.value, {})
                compliance = category_ii.get("compliance_percentage", 0)
                comfort_summary[param].append(compliance)
        
        for param, compliances in comfort_summary.items():
            building_analysis["building_comfort_summary"][param] = {
                "average_compliance": round(np.mean(compliances), 2),
                "min_compliance": round(min(compliances), 2),
                "max_compliance": round(max(compliances), 2),
                "rooms_below_80_percent": sum(1 for c in compliances if c < 80)
            }
        
        # Aggregate data quality
        quality_scores = [analysis.get("data_quality", {}).get("overall_score", 0) 
                         for analysis in room_analyses]
        
        building_analysis["data_quality_summary"] = {
            "average_quality_score": round(np.mean(quality_scores), 3),
            "rooms_below_threshold": sum(1 for score in quality_scores if score < 0.8),
            "best_quality_score": round(max(quality_scores), 3),
            "worst_quality_score": round(min(quality_scores), 3)
        }
        
        # Generate building-level recommendations
        building_analysis["building_recommendations"] = self._generate_building_recommendations(building_analysis)
        
        return building_analysis
    
    def _generate_building_recommendations(self, building_analysis: Dict[str, Any]) -> List[str]:
        """Generate building-level recommendations."""
        recommendations = []
        
        # Data quality recommendations
        data_quality = building_analysis.get("data_quality_summary", {})
        rooms_below_threshold = data_quality.get("rooms_below_threshold", 0)
        room_count = building_analysis.get("room_count", 0)
        
        if rooms_below_threshold > room_count * 0.3:
            recommendations.append(f"📊 {rooms_below_threshold} out of {room_count} rooms have poor data quality. Building-wide sensor maintenance recommended.")
        
        # Comfort recommendations
        comfort_summary = building_analysis.get("building_comfort_summary", {})
        
        for param, summary in comfort_summary.items():
            avg_compliance = summary.get("average_compliance", 100)
            rooms_below_80 = summary.get("rooms_below_80_percent", 0)
            
            if avg_compliance < 70:
                recommendations.append(f"🏢 Building-wide {param} comfort issues detected (avg: {avg_compliance:.1f}% compliance). HVAC system review recommended.")
            elif rooms_below_80 > room_count * 0.4:
                recommendations.append(f"⚠️ {rooms_below_80} rooms have {param} comfort issues. Zone-specific adjustments needed.")
        
        # Variation recommendations
        statistics = building_analysis.get("aggregated_statistics", {})
        for param, stats in statistics.items():
            variation = stats.get("room_variation", 0)
            if variation > 2.0:  # Threshold depends on parameter
                recommendations.append(f"📈 High variation in {param} across rooms (σ={variation:.1f}). Check for zoning or system balance issues.")
        
        if not recommendations:
            recommendations.append("✅ Building IEQ performance appears consistent across all monitored rooms.")
        
        return recommendations
    
    def generate_visualizations(self, ieq_data: IEQData, output_dir: Path) -> Dict[str, str]:
        """Generate visualization plots for IEQ data."""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_plots = {}
        
        try:
            # Set up the plotting style
            plt.style.use('default')
            sns.set_palette("husl")
            
            data = ieq_data.data
            measurement_columns = [col for col in data.columns 
                                 if any(param.value in col.lower() 
                                       for param in IEQParameter.get_measurement_parameters())]
            
            # 1. Time series plot
            if measurement_columns:
                fig, axes = plt.subplots(len(measurement_columns), 1, figsize=(15, 4*len(measurement_columns)))
                if len(measurement_columns) == 1:
                    axes = [axes]
                
                for i, col in enumerate(measurement_columns):
                    if data[col].count() > 0:
                        axes[i].plot(data.index, data[col], linewidth=0.8, alpha=0.7)
                        axes[i].set_title(f'{col} over Time', fontsize=12)
                        axes[i].set_ylabel(col)
                        axes[i].grid(True, alpha=0.3)
                
                plt.tight_layout()
                timeseries_path = output_dir / f"{ieq_data.room_id}_timeseries.png"
                plt.savefig(timeseries_path, dpi=300, bbox_inches='tight')
                plt.close()
                generated_plots["timeseries"] = str(timeseries_path)
            

            # 2. Daily patterns heatmap
            if len(measurement_columns) > 0:
                data_hourly = data.copy()

                if not isinstance(data.index, pd.DatetimeIndex):
                    data.index = pd.to_datetime(data.index)

                data['hour'] = data.index.hour
                data['date'] = data.index.date

                for col in measurement_columns[:2]:  # Limit to first 2 parameters
                    if data[col].count() > 10:
                        pivot_data = data_hourly.pivot_table(
                            values=col, 
                            index='date', 
                            columns='hour', 
                            aggfunc='mean'
                        )
                        
                        plt.figure(figsize=(12, 8))
                        sns.heatmap(pivot_data, cmap='RdYlBu_r', cbar_kws={'label': col})
                        plt.title(f'Daily {col} Patterns', fontsize=14)
                        plt.xlabel('Hour of Day')
                        plt.ylabel('Date')
                        
                        heatmap_path = output_dir / f"{ieq_data.room_id}_{col}_heatmap.png"
                        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        generated_plots[f"{col}_heatmap"] = str(heatmap_path)
            
            # 3. Distribution plots
            if len(measurement_columns) > 1:
                fig, axes = plt.subplots(2, (len(measurement_columns)+1)//2, figsize=(15, 8))
                axes = axes.flatten() if len(measurement_columns) > 2 else [axes] if len(measurement_columns) == 2 else axes
                
                for i, col in enumerate(measurement_columns):
                    if data[col].count() > 0 and i < len(axes):
                        axes[i].hist(data[col].dropna(), bins=30, alpha=0.7, edgecolor='black')
                        axes[i].set_title(f'{col} Distribution')
                        axes[i].set_xlabel(col)
                        axes[i].set_ylabel('Frequency')
                        axes[i].grid(True, alpha=0.3)
                
                # Hide unused subplots
                for i in range(len(measurement_columns), len(axes)):
                    axes[i].set_visible(False)
                
                plt.tight_layout()
                distribution_path = output_dir / f"{ieq_data.room_id}_distributions.png"
                plt.savefig(distribution_path, dpi=300, bbox_inches='tight')
                plt.close()
                generated_plots["distributions"] = str(distribution_path)
            
        except Exception as e:
            print(f"Error generating visualizations: {e}") #? We got an error 'date' to solve here
        
        return generated_plots
    
    def export_analysis_results(
        self, 
        room_analyses: List[Dict[str, Any]], 
        building_analysis: Dict[str, Any],
        output_dir: Path,
        formats: List[str] = ["json", "csv"]
    ) -> Dict[str, str]:
        """Export analysis results in various formats."""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        try:
            # Export individual room analyses
            if "json" in formats:
                room_analyses_path = output_dir / "room_analyses.json"
                with open(room_analyses_path, 'w') as f:
                    json.dump(room_analyses, f, indent=2, default=str)
                exported_files["room_analyses_json"] = str(room_analyses_path)
                
                building_analysis_path = output_dir / "building_analysis.json"
                with open(building_analysis_path, 'w') as f:
                    json.dump(building_analysis, f, indent=2, default=str)
                exported_files["building_analysis_json"] = str(building_analysis_path)
            
            # Export summary CSV
            if "csv" in formats and room_analyses:
                summary_data = []
                
                for analysis in room_analyses:
                    row = {
                        "room_id": analysis["room_id"],
                        "building_id": analysis["building_id"],
                        "data_quality_score": analysis.get("data_quality", {}).get("overall_score", 0),
                        "total_records": analysis.get("data_quality", {}).get("total_records", 0)
                    }
                    
                    # Add basic statistics
                    for param, stats in analysis.get("basic_statistics", {}).items():
                        row[f"{param}_mean"] = stats.get("mean", None)
                        row[f"{param}_std"] = stats.get("std", None)
                    
                    # Add comfort compliance for all EN 16798-1 categories
                    for param, categories in analysis.get("comfort_analysis", {}).items():
                        for category_name, category_data in categories.items():
                            compliance_pct = category_data.get("compliance_percentage", None)
                            compliant_hours = category_data.get("compliant_hours", None)
                            total_hours = category_data.get("total_hours", None)
                            non_compliant_hours = total_hours - compliant_hours if (total_hours and compliant_hours) else None
                            
                            # Clean category name for column headers
                            clean_category = category_name.replace(" ", "_").lower()
                            row[f"{param}_{clean_category}_compliance_pct"] = compliance_pct
                            row[f"{param}_{clean_category}_compliant_hours"] = compliant_hours
                            row[f"{param}_{clean_category}_non_compliant_hours"] = non_compliant_hours

                    # Add ACH metrics
                    ach_metrics = analysis.get("ach_metrics", {})
                    row["ach_mean"] = ach_metrics.get("ach_mean", None)
                    row["ach_median"] = ach_metrics.get("ach_median", None)
                    row["ach_std"] = ach_metrics.get("ach_std", None)
                    row["ach_min"] = ach_metrics.get("ach_min", None)
                    row["ach_max"] = ach_metrics.get("ach_max", None)
                    row["ach_confidence"] = ach_metrics.get("confidence", None)
                    row["ach_confidence_prob"] = ach_metrics.get("confidence_prob", None)
                    row["ach_ventilation_status"] = ach_metrics.get("ventilation_status", None)
                    
                    # Add custom analytics rules compliance
                    rule_based_analysis = analysis.get("rule_based_analysis", {})
                    comfort_compliance = rule_based_analysis.get("comfort_compliance", {})
                    
                    for rule_name, rule_data in comfort_compliance.items():
                        if isinstance(rule_data, dict):
                            # Clean rule name for column headers
                            clean_rule_name = rule_name.replace(" ", "_").lower()
                            compliance_rate = rule_data.get("compliance_rate", None)
                            total_points = rule_data.get("total_points", None)
                            compliant_points = rule_data.get("compliant_points", None)
                            non_compliant_hours = rule_data.get("non_compliant_hours", None)
                            
                            # Convert compliance rate to percentage
                            compliance_pct = compliance_rate * 100 if compliance_rate is not None else None
                            
                            row[f"{clean_rule_name}_compliance_pct"] = compliance_pct
                            row[f"{clean_rule_name}_total_hours"] = total_points
                            row[f"{clean_rule_name}_compliant_hours"] = compliant_points
                            row[f"{clean_rule_name}_non_compliant_hours"] = non_compliant_hours
                    
                    summary_data.append(row)
                
                summary_df = pd.DataFrame(summary_data)
                summary_path = output_dir / "ieq_analysis_summary.csv"
                summary_df.to_csv(summary_path, index=False)
                exported_files["summary_csv"] = str(summary_path)
                
        except Exception as e:
            print(f"Error exporting analysis results: {e}")
        
        return exported_files
