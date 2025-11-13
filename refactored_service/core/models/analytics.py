from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    TEST_RESULT = "test_result"
    COMPLIANCE = "compliance"
    EN16798_COMPLIANCE = "en16798_compliance"
    SIMULATION_RUN = "simulation_run"
    OTHER = "other"

class BaseAnalysis(BaseModel):
    id: str
    name: str
    type: AnalysisType
    spatial_entity_id: str
    rule_set_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    error_message: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

class TestResult(BaseAnalysis):
    type: AnalysisType = AnalysisType.TEST_RESULT
    rule_id: str
    pass_: bool = Field(..., alias="pass")
    out_of_range_hours: Optional[float] = None
    out_of_range_percentage: Optional[float] = None

class ComplianceAnalysis(BaseAnalysis):
    type: AnalysisType = AnalysisType.COMPLIANCE
    test_result_ids: List[str] = Field(default_factory=list)
    overall_pass: Optional[bool] = None
    summary_results: Dict[str, Any] = Field(default_factory=dict)

class EN16798ComplianceAnalysis(ComplianceAnalysis):
    type: AnalysisType = AnalysisType.EN16798_COMPLIANCE
    category: Optional[str] = None
    child_categories: Dict[str, str] = Field(default_factory=dict)
