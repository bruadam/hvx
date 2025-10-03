"""
Smart Recommendation Service

High-level service that orchestrates recommendation generation for
portfolios, buildings, and rooms. Integrates with the RecommendationEngine
to provide intelligent, evidence-based improvement suggestions.

Features:
- Portfolio-wide recommendation aggregation
- Building-level recommendations
- Room-specific recommendations
- Weather correlation integration
- Prerequisite test checking and auto-execution
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from dataclasses import dataclass

from src.core.models import BuildingDataset
# Use analysis_results instead of hierarchical_results
try:
    from src.core.models.results.analysis_results import AnalysisResults as HierarchicalAnalysisResult
except ImportError:
    # Fallback for type annotations
    HierarchicalAnalysisResult = Any

from src.core.analytics.ieq.RecommendationEngine import (
    RecommendationEngine,
    RecommendationResult
)


@dataclass
class PortfolioRecommendations:
    """Aggregated recommendations for entire portfolio."""
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    top_recommendations: List[RecommendationResult]
    by_building: Dict[str, List[RecommendationResult]]
    common_issues: List[str]


class SmartRecommendationService:
    """
    Service for generating smart, evidence-based recommendations.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize smart recommendation service.

        Args:
            config_dict: Optional configuration for analysis and recommendations
        """
        self.config = config_dict or {}
        self.engine = RecommendationEngine(config_dict)

    def generate_portfolio_recommendations(
        self,
        dataset: BuildingDataset,
        analysis_results: HierarchicalAnalysisResult,
        weather_data: Optional[pd.DataFrame] = None,
        auto_run_prerequisites: bool = True,
        top_n: int = 10
    ) -> PortfolioRecommendations:
        """
        Generate aggregated recommendations for entire portfolio.

        Args:
            dataset: Building dataset
            analysis_results: Hierarchical analysis results
            weather_data: Optional weather data for correlation
            auto_run_prerequisites: If True, auto-run missing prerequisite tests
            top_n: Number of top recommendations to return

        Returns:
            Portfolio-wide recommendations
        """
        all_recommendations = []
        by_building = {}

        # Generate recommendations for each building
        for building in dataset.buildings:
            building_recs = self.generate_building_recommendations(
                building,
                analysis_results,
                weather_data,
                auto_run_prerequisites
            )
            by_building[building.building_name] = building_recs
            all_recommendations.extend(building_recs)

        # Count by priority
        priority_counts = {
            'critical': sum(1 for r in all_recommendations if r.priority == 'critical'),
            'high': sum(1 for r in all_recommendations if r.priority == 'high'),
            'medium': sum(1 for r in all_recommendations if r.priority == 'medium'),
            'low': sum(1 for r in all_recommendations if r.priority == 'low')
        }

        # Sort all recommendations by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        # Get top N
        top_recommendations = all_recommendations[:top_n]

        # Identify common issues across portfolio
        common_issues = self._identify_common_issues(all_recommendations)

        return PortfolioRecommendations(
            total_recommendations=len(all_recommendations),
            critical_count=priority_counts['critical'],
            high_count=priority_counts['high'],
            medium_count=priority_counts['medium'],
            low_count=priority_counts['low'],
            top_recommendations=top_recommendations,
            by_building=by_building,
            common_issues=common_issues
        )

    def generate_building_recommendations(
        self,
        building,
        analysis_results: HierarchicalAnalysisResult,
        weather_data: Optional[pd.DataFrame] = None,
        auto_run_prerequisites: bool = True
    ) -> List[RecommendationResult]:
        """
        Generate recommendations for a single building.

        Args:
            building: Building object
            analysis_results: Analysis results
            weather_data: Optional weather data
            auto_run_prerequisites: If True, auto-run missing tests

        Returns:
            List of recommendations for the building
        """
        building_recommendations = []

        # Generate recommendations for each room
        for room in building.rooms:
            # Get room analysis results
            room_key = f"{building.building_name}_{room.room_name}"
            room_analysis = analysis_results.rooms.get(room_key)

            if room_analysis is None:
                continue

            room_recs = self.engine.generate_recommendations_for_room(
                room_data=room,
                room_analysis=room_analysis,
                weather_data=weather_data,
                auto_run_prerequisites=auto_run_prerequisites
            )

            building_recommendations.extend(room_recs)

        return building_recommendations

    def generate_room_recommendations(
        self,
        room_data,
        room_analysis,
        weather_data: Optional[pd.DataFrame] = None,
        auto_run_prerequisites: bool = True
    ) -> List[RecommendationResult]:
        """
        Generate recommendations for a single room.

        Args:
            room_data: Room data
            room_analysis: Room analysis results
            weather_data: Optional weather data
            auto_run_prerequisites: If True, auto-run missing tests

        Returns:
            List of recommendations
        """
        return self.engine.generate_recommendations_for_room(
            room_data=room_data,
            room_analysis=room_analysis,
            weather_data=weather_data,
            auto_run_prerequisites=auto_run_prerequisites
        )

    def _identify_common_issues(
        self,
        recommendations: List[RecommendationResult]
    ) -> List[str]:
        """
        Identify common issues across multiple recommendations.

        Args:
            recommendations: List of all recommendations

        Returns:
            List of common issue descriptions
        """
        # Count recommendation types
        type_counts = {}
        for rec in recommendations:
            rec_type = rec.recommendation_type
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1

        # Identify issues that appear frequently (>30% of total)
        threshold = len(recommendations) * 0.3
        common_issues = []

        issue_descriptions = {
            'solar_shading': 'Solar heat gain causing overheating',
            'ventilation': 'Inadequate ventilation causing air quality issues',
            'hvac': 'HVAC system performance problems',
            'insulation': 'Poor insulation causing temperature instability'
        }

        for issue_type, count in type_counts.items():
            if count >= threshold:
                desc = issue_descriptions.get(issue_type, issue_type)
                common_issues.append(f"{desc} (affects {count} rooms)")

        return common_issues

    def export_recommendations_to_dict(
        self,
        portfolio_recs: PortfolioRecommendations
    ) -> Dict[str, Any]:
        """
        Export recommendations to dictionary format for JSON serialization.

        Args:
            portfolio_recs: Portfolio recommendations

        Returns:
            Dictionary representation
        """
        return {
            'summary': {
                'total_recommendations': portfolio_recs.total_recommendations,
                'by_priority': {
                    'critical': portfolio_recs.critical_count,
                    'high': portfolio_recs.high_count,
                    'medium': portfolio_recs.medium_count,
                    'low': portfolio_recs.low_count
                },
                'common_issues': portfolio_recs.common_issues
            },
            'top_recommendations': [
                self._recommendation_to_dict(rec)
                for rec in portfolio_recs.top_recommendations
            ],
            'by_building': {
                building_name: [
                    self._recommendation_to_dict(rec)
                    for rec in recs
                ]
                for building_name, recs in portfolio_recs.by_building.items()
            }
        }

    def _recommendation_to_dict(self, rec: RecommendationResult) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            'type': rec.recommendation_type,
            'priority': rec.priority,
            'title': rec.title,
            'description': rec.description,
            'rationale': rec.rationale,
            'estimated_impact': rec.estimated_impact,
            'implementation_cost': rec.implementation_cost,
            'evidence': rec.evidence,
            'weather_correlations': rec.weather_correlations
        }
