from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .rules import RuleSet

class StandardDefinition(BaseModel):
    id: str
    name: str
    version: str
    standard_type: str
    category_based: bool = False
    categories: List[str] = Field(default_factory=list)

    # Raw config loaded from config.yaml for flexibility
    raw_config: Dict[str, Any] = Field(default_factory=dict)

    rulesets: List[RuleSet] = Field(default_factory=list)
