"""Use case for loading saved analysis results."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.enums.status import Status


class LoadAnalysisUseCase:
    """Use case for loading persisted analysis results from JSON files."""

    def __init__(self, base_output_dir: Path = Path("output/analyses")):
        """
        Initialize use case.

        Args:
            base_output_dir: Base directory for loading analyses
        """
        self.base_output_dir = base_output_dir

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all saved analysis sessions.

        Returns:
            List of session manifests
        """
        sessions = []
        for manifest_file in self.base_output_dir.glob("session_*.json"):
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                    sessions.append(manifest)
            except Exception as e:
                print(f"Warning: Failed to load manifest {manifest_file}: {e}")
                continue
        
        return sorted(sessions, key=lambda x: x.get('timestamp', ''), reverse=True)

    def execute_load_room_analysis(self, file_path: Path) -> Optional[RoomAnalysis]:
        """
        Load room analysis from JSON file.

        Args:
            file_path: Path to saved room analysis JSON

        Returns:
            RoomAnalysis object or None if loading fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Reconstruct RoomAnalysis (simplified - real implementation would need full reconstruction)
        # This is a placeholder - actual implementation would need to properly reconstruct all objects
        return None  # TODO: Implement full reconstruction

    def execute_load_building_analysis(self, file_path: Path) -> Optional[BuildingAnalysis]:
        """
        Load building analysis from JSON file.

        Args:
            file_path: Path to saved building analysis JSON

        Returns:
            BuildingAnalysis object or None if loading fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Reconstruct BuildingAnalysis
        return BuildingAnalysis(
            building_id=data['building_id'],
            building_name=data['building_name'],
            room_count=data['room_count'],
            level_count=data['level_count'],
            avg_compliance_rate=data['avg_compliance_rate'],
            avg_quality_score=data['avg_quality_score'],
            room_ids=data['room_ids'],
            level_ids=data['level_ids'],
            status=Status.COMPLETED,
        )

    def execute_load_session(self, session_name: str) -> Dict[str, Any]:
        """
        Load all analyses from a session.

        Args:
            session_name: Session identifier

        Returns:
            Dict with loaded analyses and metadata
        """
        manifest_path = self.base_output_dir / f"session_{session_name}.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Session not found: {session_name}")

        with open(manifest_path) as f:
            manifest = json.load(f)

        result = {
            "manifest": manifest,
            "room_analyses": [],
            "building_analysis": None,
        }

        # Load room analyses
        room_dir = Path(manifest['saved_paths']['rooms'])
        if room_dir.exists():
            for room_file in room_dir.glob("*.json"):
                # For now, just load the raw data
                with open(room_file) as f:
                    result["room_analyses"].append(json.load(f))

        # Load building analysis
        if 'building' in manifest['saved_paths']:
            building_path = Path(manifest['saved_paths']['building'])
            if building_path.exists():
                result["building_analysis"] = self.execute_load_building_analysis(building_path)

        return result
