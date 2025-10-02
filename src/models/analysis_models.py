"""
Hierarchical analysis models for room, level, building, and portfolio analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field
import json


class AnalysisSeverity(str, Enum):
    """Severity levels for analysis findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisStatus(str, Enum):
    """Analysis completion status."""
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class TestResult(BaseModel):
    """Result of a single test/rule evaluation."""
    
    test_name: str = Field(..., description="Name of the test")
    description: Optional[str] = Field(None, description="Test description")
    parameter: str = Field(..., description="Parameter being tested (temperature, co2, etc.)")
    
    # Compliance metrics
    compliance_rate: float = Field(..., description="Compliance rate as percentage (0-100)", ge=0, le=100)
    total_hours: int = Field(..., description="Total hours evaluated", ge=0)
    compliant_hours: int = Field(..., description="Hours in compliance", ge=0)
    non_compliant_hours: int = Field(..., description="Hours not in compliance", ge=0)
    
    # Threshold information
    threshold: Optional[Union[float, Dict[str, float]]] = Field(None, description="Threshold value(s) applied")
    threshold_type: Optional[str] = Field(None, description="Type of threshold (above, below, range)")
    
    # Statistics
    statistics: Dict[str, float] = Field(default_factory=dict, description="Statistical metrics")
    
    # Severity and recommendations
    severity: AnalysisSeverity = Field(default=AnalysisSeverity.INFO, description="Severity level")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    
    # Metadata
    period: Optional[str] = Field(None, description="Time period analyzed (all_year, summer, etc.)")
    filter_applied: Optional[str] = Field(None, description="Filter applied (opening_hours, etc.)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class RoomAnalysis(BaseModel):
    """Analysis results for a single room."""
    
    # Identification
    room_id: str = Field(..., description="Unique room identifier")
    room_name: str = Field(..., description="Human-readable room name")
    building_id: str = Field(..., description="Building identifier")
    level_id: Optional[str] = Field(None, description="Level/floor identifier")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    data_period_start: Optional[datetime] = Field(None, description="Start of analyzed data period")
    data_period_end: Optional[datetime] = Field(None, description="End of analyzed data period")
    status: AnalysisStatus = Field(default=AnalysisStatus.COMPLETED, description="Analysis status")
    
    # Test results
    test_results: Dict[str, TestResult] = Field(default_factory=dict, description="Results by test name")
    
    # Overall metrics
    overall_compliance_rate: float = Field(default=0.0, description="Overall compliance rate", ge=0, le=100)
    overall_quality_score: float = Field(default=0.0, description="Overall data quality score", ge=0, le=100)
    
    # Data quality
    data_completeness: float = Field(default=0.0, description="Data completeness percentage", ge=0, le=100)
    parameters_analyzed: List[str] = Field(default_factory=list, description="Parameters included in analysis")
    
    # Aggregated statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Stats by parameter")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues found")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def add_test_result(self, test_name: str, result: TestResult) -> None:
        """Add a test result."""
        self.test_results[test_name] = result
    
    def calculate_overall_metrics(self) -> None:
        """Calculate overall compliance and quality metrics."""
        if self.test_results:
            compliance_rates = [r.compliance_rate for r in self.test_results.values()]
            self.overall_compliance_rate = sum(compliance_rates) / len(compliance_rates)
    
    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def load_from_json(cls, filepath: Path) -> 'RoomAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class LevelAnalysis(BaseModel):
    """Aggregated analysis results for a building level/floor."""
    
    # Identification
    level_id: str = Field(..., description="Unique level identifier")
    level_name: str = Field(..., description="Human-readable level name")
    building_id: str = Field(..., description="Building identifier")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: AnalysisStatus = Field(default=AnalysisStatus.COMPLETED, description="Analysis status")
    
    # Room references
    room_ids: List[str] = Field(default_factory=list, description="IDs of rooms on this level")
    room_count: int = Field(default=0, description="Number of rooms analyzed")
    
    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Average compliance rate", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Average data quality score", ge=0, le=100)
    
    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results (avg, min, max, etc.)"
    )
    
    # Room rankings
    best_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing rooms"
    )
    worst_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rooms needing attention"
    )
    
    # Statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Aggregated statistics")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues at level")
    recommendations: List[str] = Field(default_factory=list, description="Level-wide recommendations")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def load_from_json(cls, filepath: Path) -> 'LevelAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class BuildingAnalysis(BaseModel):
    """Aggregated analysis results for a building."""
    
    # Identification
    building_id: str = Field(..., description="Unique building identifier")
    building_name: str = Field(..., description="Human-readable building name")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: AnalysisStatus = Field(default=AnalysisStatus.COMPLETED, description="Analysis status")
    
    # Structure references
    level_ids: List[str] = Field(default_factory=list, description="IDs of levels in building")
    room_ids: List[str] = Field(default_factory=list, description="IDs of all rooms in building")
    level_count: int = Field(default=0, description="Number of levels")
    room_count: int = Field(default=0, description="Number of rooms analyzed")
    
    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Average compliance rate", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Average data quality score", ge=0, le=100)
    
    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results across building"
    )
    
    # Level comparisons
    level_comparisons: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Comparison of levels"
    )
    
    # Rankings
    best_performing_levels: List[Dict[str, Any]] = Field(default_factory=list, description="Best levels")
    worst_performing_levels: List[Dict[str, Any]] = Field(default_factory=list, description="Worst levels")
    best_performing_rooms: List[Dict[str, Any]] = Field(default_factory=list, description="Best rooms")
    worst_performing_rooms: List[Dict[str, Any]] = Field(default_factory=list, description="Worst rooms")
    
    # Statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Building-wide statistics")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical building issues")
    recommendations: List[str] = Field(default_factory=list, description="Building-wide recommendations")
    
    # Climate correlation (if available)
    climate_correlations: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlations with outdoor climate"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def load_from_json(cls, filepath: Path) -> 'BuildingAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class PortfolioAnalysis(BaseModel):
    """Aggregated analysis results for a portfolio of buildings."""
    
    # Identification
    portfolio_name: str = Field(..., description="Portfolio name")
    portfolio_id: Optional[str] = Field(None, description="Portfolio identifier")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: AnalysisStatus = Field(default=AnalysisStatus.COMPLETED, description="Analysis status")
    
    # Structure references
    building_ids: List[str] = Field(default_factory=list, description="IDs of buildings in portfolio")
    building_count: int = Field(default=0, description="Number of buildings")
    total_room_count: int = Field(default=0, description="Total rooms across portfolio")
    total_level_count: int = Field(default=0, description="Total levels across portfolio")
    
    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Portfolio average compliance", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Portfolio average quality", ge=0, le=100)
    
    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results across portfolio"
    )
    
    # Building comparisons
    building_comparisons: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Comparison of buildings"
    )
    
    # Rankings
    best_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Best performing buildings"
    )
    worst_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Buildings needing attention"
    )
    
    # Benchmark statistics
    benchmark_statistics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Benchmark stats across portfolio"
    )
    
    # Portfolio-wide insights
    portfolio_trends: Dict[str, Any] = Field(default_factory=dict, description="Trends across portfolio")
    common_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Common issues found")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical portfolio issues")
    recommendations: List[str] = Field(default_factory=list, description="Portfolio-wide recommendations")
    
    # Investment priorities
    investment_priorities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Prioritized investment recommendations"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def load_from_json(cls, filepath: Path) -> 'PortfolioAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class AnalysisResults(BaseModel):
    """Container for all analysis results."""
    
    portfolio: Optional[PortfolioAnalysis] = Field(None, description="Portfolio-level analysis")
    buildings: Dict[str, BuildingAnalysis] = Field(default_factory=dict, description="Building analyses by ID")
    levels: Dict[str, LevelAnalysis] = Field(default_factory=dict, description="Level analyses by ID")
    rooms: Dict[str, RoomAnalysis] = Field(default_factory=dict, description="Room analyses by ID")
    
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")
    
    def get_room_analysis(self, room_id: str) -> Optional[RoomAnalysis]:
        """Get room analysis by ID."""
        return self.rooms.get(room_id)
    
    def get_level_analysis(self, level_id: str) -> Optional[LevelAnalysis]:
        """Get level analysis by ID."""
        return self.levels.get(level_id)
    
    def get_building_analysis(self, building_id: str) -> Optional[BuildingAnalysis]:
        """Get building analysis by ID."""
        return self.buildings.get(building_id)
    
    def save_all_to_directory(self, output_dir: Path) -> None:
        """Save all analyses to a directory structure."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save portfolio
        if self.portfolio:
            portfolio_file = output_dir / "portfolio_analysis.json"
            self.portfolio.save_to_json(portfolio_file)
        
        # Save buildings
        buildings_dir = output_dir / "buildings"
        buildings_dir.mkdir(exist_ok=True)
        for building_id, analysis in self.buildings.items():
            building_file = buildings_dir / f"{building_id}.json"
            analysis.save_to_json(building_file)
        
        # Save levels
        levels_dir = output_dir / "levels"
        levels_dir.mkdir(exist_ok=True)
        for level_id, analysis in self.levels.items():
            level_file = levels_dir / f"{level_id}.json"
            analysis.save_to_json(level_file)
        
        # Save rooms
        rooms_dir = output_dir / "rooms"
        rooms_dir.mkdir(exist_ok=True)
        for room_id, analysis in self.rooms.items():
            room_file = rooms_dir / f"{room_id}.json"
            analysis.save_to_json(room_file)
