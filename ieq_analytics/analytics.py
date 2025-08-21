"""
Simplified IEQ Analytics Module

Streamlined analytics module that leverages the unified analytics engine
for all analysis operations and focuses on data export functionality.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import IEQData
from .unified_analytics import UnifiedAnalyticsEngine, AnalysisType

import logging
logger = logging.getLogger(__name__)


class IEQAnalytics:
    """Simplified analytics engine focused on analysis and export functionality."""
    
    def __init__(self, rules_config_path: Optional[Path] = None):
        """Initialize analytics engine with unified backend."""
        if rules_config_path is None:
            rules_config_path = Path(__file__).parent.parent / "config" / "tests.yaml"
        
        # Initialize unified analytics engine
        self.unified_engine = UnifiedAnalyticsEngine(rules_config_path)
        
        # Load EN16798 config if available
        en16798_path = Path(__file__).parent.parent / "config" / "en16798_opening_hours_rules.yaml"
        if en16798_path.exists():
            self.en16798_engine = UnifiedAnalyticsEngine(en16798_path)
        else:
            self.en16798_engine = None
    
    def analyze_room_data(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Comprehensive analysis of a single room's IEQ data."""
        
        # Base analysis using unified engine
        analysis_results = self.unified_engine.analyze_room_data(
            ieq_data.data,
            ieq_data.room_id,
            analysis_types=[
                AnalysisType.BASIC_STATISTICS,
                AnalysisType.DATA_QUALITY,
                AnalysisType.USER_RULES
            ]
        )
        
        # Add room and building metadata
        analysis_results.update({
            "room_id": ieq_data.room_id,
            "building_id": ieq_data.building_id,
            "data_period": {
                "start": ieq_data.data_period_start.isoformat() if ieq_data.data_period_start else None,
                "end": ieq_data.data_period_end.isoformat() if ieq_data.data_period_end else None,
                "duration_days": (ieq_data.data_period_end - ieq_data.data_period_start).days if ieq_data.data_period_start and ieq_data.data_period_end else None
            }
        })
        
        # Add EN16798 analysis if available
        if self.en16798_engine:
            try:
                en16798_analysis = self.en16798_engine.analyze_room_data(
                    ieq_data.data,
                    ieq_data.room_id,
                    analysis_types=[AnalysisType.EN16798_COMPLIANCE]
                )
                analysis_results["en16798_compliance"] = en16798_analysis.get("en16798_compliance", {})
            except Exception as e:
                logger.error(f"Error in EN16798 analysis: {e}")
                analysis_results["en16798_compliance"] = {}
        
        # Generate recommendations
        analysis_results["recommendations"] = self._generate_recommendations(analysis_results)
        
        return analysis_results
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Data quality recommendations
        data_quality = analysis_results.get("data_quality", {})
        overall_score = data_quality.get("overall_score", 0)
        
        if overall_score < 0.7:
            recommendations.append("⚠️ Data quality is below acceptable threshold. Consider sensor maintenance and data validation.")
        elif overall_score < 0.9:
            recommendations.append("💡 Data quality could be improved. Check for missing data periods and sensor calibration.")
        
        # User rules recommendations
        user_rules = analysis_results.get("user_rules", {})
        poor_compliance_rules = [
            rule_name for rule_name, rule_result in user_rules.items()
            if isinstance(rule_result, dict) and rule_result.get("compliance_rate", 100) < 70
        ]
        
        if poor_compliance_rules:
            recommendations.append(f"❌ Poor compliance detected for rules: {', '.join(poor_compliance_rules[:3])}")
        
        # EN16798 recommendations
        en16798_results = analysis_results.get("en16798_compliance", {})
        if en16798_results and isinstance(en16798_results, dict):
            poor_en16798 = [
                rule_name for rule_name, rule_result in en16798_results.items()
                if isinstance(rule_result, dict) and rule_result.get("compliance_rate", 100) < 80
            ]
            if poor_en16798:
                recommendations.append(f"📏 EN16798 compliance issues in: {', '.join(poor_en16798[:2])}")
        
        # Default recommendation if no issues found
        if not recommendations:
            recommendations.append("✅ Room performance is within acceptable ranges. Continue regular monitoring.")
        
        return recommendations
    
    def aggregate_building_analysis(self, room_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate room-level analyses into building-level summary."""
        if not room_analyses:
            return {"error": "No room analyses provided"}
        
        building_id = room_analyses[0].get("building_id", "unknown")
        
        # Calculate aggregated statistics
        all_stats = {}
        for analysis in room_analyses:
            basic_stats = analysis.get("basic_statistics", {})
            for param, stats in basic_stats.items():
                if param not in all_stats:
                    all_stats[param] = []
                if isinstance(stats, dict) and "mean" in stats:
                    all_stats[param].append(stats["mean"])
        
        aggregated_stats = {}
        for param, values in all_stats.items():
            if values:
                aggregated_stats[param] = {
                    "building_mean": round(np.mean(values), 2),
                    "building_std": round(np.std(values), 2),
                    "min_room_mean": round(min(values), 2),
                    "max_room_mean": round(max(values), 2),
                    "room_count": len(values)
                }
        
        # Aggregate data quality
        quality_scores = [
            analysis.get("data_quality", {}).get("overall_score", 0) 
            for analysis in room_analyses
        ]
        
        # Aggregate compliance
        compliance_summary = {}
        for analysis in room_analyses:
            user_rules = analysis.get("user_rules", {})
            for rule_name, rule_result in user_rules.items():
                if isinstance(rule_result, dict) and "compliance_rate" in rule_result:
                    if rule_name not in compliance_summary:
                        compliance_summary[rule_name] = []
                    compliance_summary[rule_name].append(rule_result["compliance_rate"])
        
        building_compliance = {}
        for rule_name, compliance_rates in compliance_summary.items():
            building_compliance[rule_name] = {
                "average_compliance": round(np.mean(compliance_rates), 2),
                "rooms_analyzed": len(compliance_rates),
                "rooms_below_80_percent": sum(1 for rate in compliance_rates if rate < 80)
            }
        
        return {
            "building_id": building_id,
            "room_count": len(room_analyses),
            "analysis_timestamp": datetime.now().isoformat(),
            "aggregated_statistics": aggregated_stats,
            "building_compliance_summary": building_compliance,
            "data_quality_summary": {
                "average_quality_score": round(np.mean(quality_scores), 3) if quality_scores else 0,
                "rooms_below_threshold": sum(1 for score in quality_scores if score < 0.8),
                "quality_range": {
                    "best": round(max(quality_scores), 3) if quality_scores else 0,
                    "worst": round(min(quality_scores), 3) if quality_scores else 0
                }
            },
            "rooms": [analysis["room_id"] for analysis in room_analyses]
        }
    
    def export_to_csv(self, room_analyses: List[Dict[str, Any]], output_path: Path) -> str:
        """Export room analyses to CSV format with detailed compliance data."""
        output_path = Path(output_path)
        
        # Prepare data for CSV
        csv_data = []
        for analysis in room_analyses:
            row = {
                "room_id": analysis.get("room_id", ""),
                "building_id": analysis.get("building_id", ""),
                "data_period_start": analysis.get("data_period", {}).get("start", ""),
                "data_period_end": analysis.get("data_period", {}).get("end", ""),
                "duration_days": analysis.get("data_period", {}).get("duration_days", 0),
                "data_quality_score": analysis.get("data_quality", {}).get("overall_score", 0),
                "total_records": analysis.get("data_quality", {}).get("total_records", 0)
            }
            
            # Add basic statistics
            basic_stats = analysis.get("basic_statistics", {})
            for param, stats in basic_stats.items():
                if isinstance(stats, dict):
                    row[f"{param}_mean"] = stats.get("mean", 0)
                    row[f"{param}_std"] = stats.get("std", 0)
                    row[f"{param}_min"] = stats.get("min", 0)
                    row[f"{param}_max"] = stats.get("max", 0)
            
            # Add compliance rates from user_rules (which includes analytics rules)
            user_rules = analysis.get("user_rules", {})
            compliance_rates = []
            for rule_name, rule_result in user_rules.items():
                if isinstance(rule_result, dict) and "compliance_rate" in rule_result:
                    compliance_rate = rule_result.get("compliance_rate", 0)
                    row[f"rule_{rule_name}_compliance"] = compliance_rate
                    row[f"rule_{rule_name}_violations"] = rule_result.get("violations_count", 0)
                    compliance_rates.append(compliance_rate)
            
            # Add average compliance rate
            if compliance_rates:
                row["average_compliance_rate"] = sum(compliance_rates) / len(compliance_rates)
            else:
                row["average_compliance_rate"] = 0
            
            csv_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def export_to_json(self, room_analyses: List[Dict[str, Any]], building_analysis: Dict[str, Any], output_path: Path) -> str:
        """Export analyses to JSON format with detailed compliance data."""
        output_path = Path(output_path)
        
        # Calculate summary statistics
        total_rules = 0
        total_compliance_rate = 0
        rooms_with_analysis = 0
        
        for analysis in room_analyses:
            user_rules = analysis.get("user_rules", {})
            if user_rules:
                rooms_with_analysis += 1
                compliance_rates = []
                for rule_name, rule_result in user_rules.items():
                    if isinstance(rule_result, dict) and "compliance_rate" in rule_result:
                        compliance_rates.append(rule_result.get("compliance_rate", 0))
                        total_rules += 1
                
                if compliance_rates:
                    total_compliance_rate += sum(compliance_rates) / len(compliance_rates)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_rooms": len(room_analyses),
                "rooms_with_rule_analysis": rooms_with_analysis,
                "total_rules_evaluated": total_rules,
                "average_overall_compliance": round(total_compliance_rate / rooms_with_analysis, 2) if rooms_with_analysis > 0 else 0,
                "building_count": 1 if building_analysis else 0
            },
            "room_analyses": room_analyses,
            "building_analysis": building_analysis
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return str(output_path)
    
    def get_available_analysis_types(self) -> List[str]:
        """Get list of available analysis types."""
        return [at.value for at in AnalysisType]
    
    def get_available_rules(self) -> Dict[str, List[str]]:
        """Get available rules from unified engine."""
        try:
            return self.unified_engine.get_available_rules()
        except Exception as e:
            logger.error(f"Error getting available rules: {e}")
            return {"user_rules": [], "en16798_rules": [], "all_rules": []}
    
    def apply_filters(self, ieq_data: IEQData, filter_name: str = 'all_hours', period_name: str = 'all_year') -> IEQData:
        """Apply time-based filters to IEQData and return filtered copy."""
        try:
            # Get filter processor from unified engine
            filter_processor = getattr(self.unified_engine, 'filter_processor', None)
            if filter_processor:
                filtered_df = filter_processor.apply_filter(
                    ieq_data.data, 
                    filter_name=filter_name, 
                    period_name=period_name
                )
            else:
                # Fallback to original data if no filter processor
                filtered_df = ieq_data.data
            
            # Create new IEQData with filtered data
            return IEQData(
                room_id=ieq_data.room_id,
                building_id=ieq_data.building_id,
                data=filtered_df,
                quality_score=ieq_data.quality_score,
                data_period_start=filtered_df.index.min() if not filtered_df.empty else ieq_data.data_period_start,
                data_period_end=filtered_df.index.max() if not filtered_df.empty else ieq_data.data_period_end
            )
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return ieq_data
