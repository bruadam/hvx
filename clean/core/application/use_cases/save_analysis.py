"""Use case for saving analysis results to disk."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis


class SaveAnalysisUseCase:
    """Use case for persisting analysis results to JSON files."""

    def __init__(self, base_output_dir: Path = Path("output/analyses")):
        """
        Initialize use case.

        Args:
            base_output_dir: Base directory for saving analyses
        """
        self.base_output_dir = base_output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def execute_save_room_analysis(
        self,
        room_analysis: RoomAnalysis,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Save room analysis to JSON file.

        Args:
            room_analysis: RoomAnalysis to save
            output_path: Optional custom output path

        Returns:
            Path to saved file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"room_{room_analysis.room_id}_{timestamp}.json"
            output_path = self.base_output_dir / "rooms" / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = self._room_analysis_to_dict(room_analysis)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    def execute_save_building_analysis(
        self,
        building_analysis: BuildingAnalysis,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Save building analysis to JSON file.

        Args:
            building_analysis: BuildingAnalysis to save
            output_path: Optional custom output path

        Returns:
            Path to saved file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"building_{building_analysis.building_id}_{timestamp}.json"
            output_path = self.base_output_dir / "buildings" / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = self._building_analysis_to_dict(building_analysis)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    def execute_save_batch(
        self,
        room_analyses: List[RoomAnalysis],
        building_analysis: Optional[BuildingAnalysis] = None,
        session_name: Optional[str] = None,
    ) -> Dict[str, Path]:
        """
        Save multiple analyses in a batch.

        Args:
            room_analyses: List of room analyses
            building_analysis: Optional building analysis
            session_name: Optional session identifier

        Returns:
            Dict mapping analysis types to saved paths
        """
        if session_name is None:
            session_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        saved_paths = {}

        # Save room analyses
        room_dir = self.base_output_dir / "rooms" / session_name
        room_dir.mkdir(parents=True, exist_ok=True)
        
        for ra in room_analyses:
            filename = f"{ra.room_id}.json"
            path = room_dir / filename
            data = self._room_analysis_to_dict(ra)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        saved_paths['rooms'] = room_dir

        # Save building analysis
        if building_analysis:
            building_dir = self.base_output_dir / "buildings"
            building_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{building_analysis.building_id}_{session_name}.json"
            path = building_dir / filename
            data = self._building_analysis_to_dict(building_analysis)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            saved_paths['building'] = path

        # Save session manifest
        manifest_path = self.base_output_dir / f"session_{session_name}.json"
        manifest = {
            "session_name": session_name,
            "timestamp": datetime.now().isoformat(),
            "room_analyses_count": len(room_analyses),
            "has_building_analysis": building_analysis is not None,
            "saved_paths": {k: str(v) for k, v in saved_paths.items()},
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        saved_paths['manifest'] = manifest_path

        return saved_paths

    def _room_analysis_to_dict(self, ra: RoomAnalysis) -> Dict[str, Any]:
        """Convert RoomAnalysis to JSON-serializable dict."""
        return {
            "room_id": ra.room_id,
            "room_name": ra.room_name,
            "level_id": ra.level_id,
            "building_id": ra.building_id,
            "analysis_timestamp": ra.analysis_timestamp.isoformat() if ra.analysis_timestamp else None,
            "overall_compliance_rate": ra.overall_compliance_rate,
            "data_quality_score": ra.data_quality_score,
            "data_completeness": ra.data_completeness,
            "test_count": ra.test_count,
            "passed_tests": ra.passed_tests,
            "failed_tests": ra.failed_tests,
            "compliance_results": {
                test_id: {
                    "test_id": result.test_id,
                    "parameter": result.parameter.value if hasattr(result.parameter, 'value') else str(result.parameter),
                    "standard": result.standard.value if hasattr(result.standard, 'value') else str(result.standard),
                    "compliance_rate": result.compliance_rate,
                    "violations_count": result.violations_count,
                }
                for test_id, result in ra.compliance_results.items()
            },
            "parameter_statistics": ra.parameter_statistics,
        }

    def _building_analysis_to_dict(self, ba: BuildingAnalysis) -> Dict[str, Any]:
        """Convert BuildingAnalysis to JSON-serializable dict."""
        return {
            "building_id": ba.building_id,
            "building_name": ba.building_name,
            "analysis_timestamp": ba.analysis_timestamp.isoformat() if ba.analysis_timestamp else None,
            "room_count": ba.room_count,
            "level_count": ba.level_count,
            "avg_compliance_rate": ba.avg_compliance_rate,
            "avg_quality_score": ba.avg_quality_score,
            "room_ids": ba.room_ids,
            "level_ids": ba.level_ids,
        }
