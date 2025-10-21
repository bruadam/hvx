"""EN 16798-1 standard aggregator."""

from typing import List, Dict, Any, Optional

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.value_objects.recommendation import Recommendation
from core.domain.enums.priority import Priority


class EN16798Aggregator:
    """
    EN 16798-1 specific compliance aggregation.
    
    EN 16798-1 defines three categories (I, II, III) where:
    - Category I = Highest performance (most strict requirements)
    - Category II = Medium performance
    - Category III = Basic/Acceptable performance (least strict requirements)
    
    Hierarchy: If Category I is achieved, Categories II and III are automatically achieved.
    
    A room complies with a category if ALL tests in that category pass (≥95% compliance).
    The "overall compliance" is determined by the highest category achieved.
    """

    COMPLIANCE_THRESHOLD = 95.0  # 95% per test to pass
    CATEGORIES = ["i", "ii", "iii"]
    CATEGORY_NAMES = {
        "i": "Category I (Highest Performance)",
        "ii": "Category II (Medium Performance)",
        "iii": "Category III (Basic/Acceptable Performance)",
    }
    # Hierarchy: lower index = higher performance
    CATEGORY_HIERARCHY = {"i": 3, "ii": 2, "iii": 1} 

    @staticmethod
    def get_en16798_compliance(room_analysis: RoomAnalysis) -> Dict[str, Any]:
        """
        Determine EN 16798-1 category compliance for a room.

        Args:
            room_analysis: Room analysis with compliance results

        Returns:
            Dictionary with:
                - highest_category: Best category achieved (i, ii, iii, or None)
                - category_compliance: Dict[str, bool] showing pass/fail for each category
                - category_details: Dict with details for each category
                - overall_compliance_rate: Rate of highest category achieved
        """
        # Group tests by category
        category_tests = EN16798Aggregator._group_tests_by_category(
            room_analysis.compliance_results
        )

        # Evaluate each category
        category_compliance = {}
        category_details = {}

        for category in EN16798Aggregator.CATEGORIES:
            if category in category_tests:
                tests = category_tests[category]
                compliant, details = EN16798Aggregator._evaluate_category(
                    category, tests
                )
                category_compliance[category] = compliant
                category_details[category] = details
            else:
                category_compliance[category] = None
                category_details[category] = {
                    "tests_count": 0,
                    "status": "not_tested",
                }

        # Find highest achieved category
        # Category I is best (highest performance), then II, then III
        highest_category = None
        highest_performance = 0  # i=3, ii=2, iii=1
        highest_compliance_rate = 0.0

        for category in EN16798Aggregator.CATEGORIES:
            if category_compliance.get(category) is True:
                performance_level = EN16798Aggregator.CATEGORY_HIERARCHY.get(category, 0)
                if performance_level > highest_performance:
                    highest_category = category
                    highest_performance = performance_level
                    if category in category_details:
                        rates = [
                            t.compliance_rate
                            for t in category_tests.get(category, [])
                        ]
                        highest_compliance_rate = (
                            min(rates) if rates else 0.0
                        )  # Lowest rate in category

        return {
            "highest_category": highest_category,
            "category_compliance": category_compliance,
            "category_details": category_details,
            "overall_compliance_rate": highest_compliance_rate,
            "total_tests": len(room_analysis.compliance_results),
        }

    @staticmethod
    def _group_tests_by_category(
        compliance_results: Dict[str, Any]
    ) -> Dict[str, List[Any]]:
        """Group compliance results by EN 16798-1 category."""
        grouped = {"i": [], "ii": [], "iii": []}

        for test_id, result in compliance_results.items():
            if test_id.startswith("cat_i_") and not test_id.startswith("cat_ii_"):
                grouped["i"].append(result)
            elif test_id.startswith("cat_ii_"):
                grouped["ii"].append(result)
            elif test_id.startswith("cat_iii_"):
                grouped["iii"].append(result)

        return grouped

    @staticmethod
    def _evaluate_category(
        category: str, test_results: List[Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Evaluate if a category is achieved.

        A category is achieved if ALL tests in that category meet the compliance threshold.

        Returns:
            (is_compliant, details_dict)
        """
        if not test_results:
            return False, {
                "tests_count": 0,
                "status": "no_tests",
            }

        # Check if all tests meet threshold
        compliant_tests = sum(
            1 for test in test_results
            if test.compliance_rate >= EN16798Aggregator.COMPLIANCE_THRESHOLD
        )
        all_compliant = compliant_tests == len(test_results)

        # Calculate minimum rate (the limiting factor)
        min_rate = min(
            (test.compliance_rate for test in test_results),
            default=0.0,
        )
        max_rate = max(
            (test.compliance_rate for test in test_results),
            default=0.0,
        )
        avg_rate = (
            sum(test.compliance_rate for test in test_results)
            / len(test_results)
        )

        return all_compliant, {
            "tests_count": len(test_results),
            "compliant_tests": compliant_tests,
            "status": "compliant" if all_compliant else "non_compliant",
            "min_rate": round(min_rate, 2),
            "max_rate": round(max_rate, 2),
            "avg_rate": round(avg_rate, 2),
            "threshold": EN16798Aggregator.COMPLIANCE_THRESHOLD,
            "test_ids": [
                test.test_id for test in test_results
            ],
        }

    @staticmethod
    def generate_en16798_recommendations(
        room_analysis: RoomAnalysis,
        en16798_compliance: Dict[str, Any],
    ) -> List[Recommendation]:
        """
        Generate EN 16798-1 specific recommendations.

        Args:
            room_analysis: Room analysis data
            en16798_compliance: Output from get_en16798_compliance

        Returns:
            List of recommendations
        """
        recommendations = []
        highest_category = en16798_compliance["highest_category"]
        category_details = en16798_compliance["category_details"]

        # Congratulations if compliant to a category
        if highest_category:
            category_name = EN16798Aggregator.CATEGORY_NAMES[highest_category]
            recommendations.append(
                Recommendation(
                    title=f"Room meets EN 16798-1 {category_name}",
                    description=f"The room complies with all thresholds for {category_name}.",
                    priority=Priority.LOW,
                )
            )

        # Identify which category failed and why
        for category in EN16798Aggregator.CATEGORIES:
            if (
                category_details.get(category, {}).get("status")
                == "non_compliant"
            ):
                failing_tests = category_details[category].get("test_ids", [])
                min_rate = category_details[category].get("min_rate", 0)

                if failing_tests:
                    recommendations.append(
                        Recommendation(
                            title=f"Category {category.upper()} not achieved - {min_rate:.1f}% compliance",
                            description=f"Failing tests in category {category.upper()}: {', '.join(failing_tests)}. "
                            f"Minimum compliance rate: {min_rate:.1f}% (need {EN16798Aggregator.COMPLIANCE_THRESHOLD}%)",
                            priority=Priority.MEDIUM if category == "i" else Priority.LOW,
                        )
                    )

        return recommendations
