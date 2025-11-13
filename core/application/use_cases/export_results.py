"""Use case for exporting analysis results."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room_analysis import RoomAnalysis


class ExportResultsUseCase:
    """Use case for exporting analysis results to various formats."""

    def execute_export_json(
        self,
        room_analyses: list[RoomAnalysis],
        building_analysis: BuildingAnalysis | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """
        Export results to JSON.

        Args:
            room_analyses: List of room analyses
            building_analysis: Optional building analysis
            output_path: Optional custom output path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output/exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"analysis_{timestamp}.json"

        data = {
            "export_timestamp": datetime.now().isoformat(),
            "building_analysis": self._building_to_dict(building_analysis) if building_analysis else None,
            "room_analyses": [self._room_analysis_to_dict(ra) for ra in room_analyses],
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    def execute_export_csv(
        self,
        room_analyses: list[RoomAnalysis],
        output_path: Path | None = None,
    ) -> Path:
        """
        Export room analyses to CSV.

        Args:
            room_analyses: List of room analyses
            output_path: Optional custom output path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output/exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"analysis_{timestamp}.csv"

        data = []
        for ra in room_analyses:
            data.append({
                "room_id": ra.room_id,
                "room_name": ra.room_name,
                "building_id": ra.building_id,
                "level_id": ra.level_id,
                "compliance_rate": ra.overall_compliance_rate,
                "data_quality": ra.data_quality_score,
                "tests_passed": len(ra.passed_tests),
                "tests_total": ra.test_count,
            })

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

        return output_path

    def execute_export_excel(
        self,
        room_analyses: list[RoomAnalysis],
        building_analysis: BuildingAnalysis | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """
        Export results to Excel with multiple sheets.

        Args:
            room_analyses: List of room analyses
            building_analysis: Optional building analysis
            output_path: Optional custom output path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output/exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"analysis_{timestamp}.xlsx"

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Building summary sheet
            if building_analysis:
                building_data = [{
                    "Building ID": building_analysis.building_id,
                    "Building Name": building_analysis.building_name,
                    "Rooms": building_analysis.room_count,
                    "Levels": building_analysis.level_count,
                    "Avg Compliance": building_analysis.avg_compliance_rate,
                    "Avg Quality": building_analysis.avg_quality_score,
                }]
                df_building = pd.DataFrame(building_data)
                df_building.to_excel(writer, sheet_name="Building Summary", index=False)

            # Room analyses sheet
            room_data = []
            for ra in room_analyses:
                room_data.append({
                    "Room ID": ra.room_id,
                    "Room Name": ra.room_name,
                    "Building ID": ra.building_id,
                    "Level ID": ra.level_id,
                    "Compliance %": ra.overall_compliance_rate,
                    "Quality Score": ra.data_quality_score,
                    "Tests Passed": len(ra.passed_tests),
                    "Tests Total": ra.test_count,
                })
            df_rooms = pd.DataFrame(room_data)
            df_rooms.to_excel(writer, sheet_name="Room Analyses", index=False)

        return output_path

    def _room_analysis_to_dict(self, ra: RoomAnalysis) -> dict:
        """Convert RoomAnalysis to dict."""
        return {
            "room_id": ra.room_id,
            "room_name": ra.room_name,
            "compliance_rate": ra.overall_compliance_rate,
            "quality_score": ra.data_quality_score,
            "tests_passed": len(ra.passed_tests),
            "tests_total": ra.test_count,
        }

    def _building_to_dict(self, ba: BuildingAnalysis) -> dict:
        """Convert BuildingAnalysis to dict."""
        return {
            "building_id": ba.building_id,
            "building_name": ba.building_name,
            "room_count": ba.room_count,
            "avg_compliance_rate": ba.avg_compliance_rate,
            "avg_quality_score": ba.avg_quality_score,
        }
