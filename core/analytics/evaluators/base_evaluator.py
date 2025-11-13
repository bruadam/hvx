"""Base evaluator interface."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.models.compliance_result import ComplianceResult


class BaseEvaluator(ABC):
    """
    Abstract base class for compliance evaluators.

    All evaluators must implement the evaluate method.
    """

    def __init__(self, standard: StandardType):
        """
        Initialize evaluator.

        Args:
            standard: The standard this evaluator implements
        """
        self.standard = standard

    @abstractmethod
    def evaluate(
        self,
        data: pd.Series,
        parameter: ParameterType,
        test_id: str,
        **kwargs: Any
    ) -> ComplianceResult:
        """
        Evaluate compliance for given data.

        Args:
            data: Time series data to evaluate
            parameter: Parameter being evaluated
            test_id: Unique test identifier
            **kwargs: Additional evaluation parameters

        Returns:
            ComplianceResult with evaluation results
        """
        pass

    def get_standard(self) -> StandardType:
        """Get the standard this evaluator implements."""
        return self.standard

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(standard={self.standard.value})"
