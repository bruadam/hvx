"""Base entity models for domain objects.

Provides common identity, metadata, and hierarchy management for all entities.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.domain.models.analysis.room_analysis import RoomAnalysis
    from core.domain.models.analysis.building_analysis import BuildingAnalysis


TChild = TypeVar("TChild")


class BaseEntity(BaseModel, Generic[TChild]):
    """
    Base entity with identity and metadata.

    All domain entities (Room, Building, etc.) inherit common structure:
    - Unique identifier
    - Human-readable name
    - Custom attributes for extensibility
    - Optional timestamps for auditing
    - Physical properties (area, volume, occupancy, etc.)
    - Standard summary and string representations

    Generic type TChild represents the type of child entities (e.g., Room has ComplianceResult children).
    """

    # Identity
    id: str = Field(..., description="Unique entity identifier")
    name: str = Field(..., description="Human-readable entity name")

    # Physical properties (can be set directly or computed from children)
    area: float | None = Field(default=None, ge=0, description="Floor area in m²")
    volume: float | None = Field(default=None, ge=0, description="Volume in m³")
    occupancy: int | None = Field(default=None, ge=0, description="Typical occupancy count")
    glass_to_wall_ratio: float | None = Field(
        default=None, ge=0, le=1, description="Ratio of glass area to wall area"
    )
    orientations: list[float] | None = Field(
        default=None,
        description="List of wall orientations in degrees (0-360), 0=North clockwise"
    )
    window_areas: list[float] | None = Field(
        default=None, description="List of window areas corresponding to orientations in m²"
    )
    shading_factors: list[float] | None = Field(
        default=None, description="List of shading factors (0-1) corresponding to orientations"
    )
    last_renovation_year: int | None = Field(
        default=None, ge=1800, le=2100, description="Year of last renovation"
    )

    # Extensibility
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom attributes and metadata"
    )

    # Optional auditing timestamps
    created_at: datetime | None = Field(
        default=None,
        description="When entity was created"
    )
    updated_at: datetime | None = Field(
        default=None,
        description="When entity was last updated"
    )
    
    # Optional computed analysis results
    # Entities can compute and cache their own metrics/compliance
    computed_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Computed metrics and analysis results (EN16798, TAIL, EPC, etc.)",
        exclude=True  # Don't serialize by default to avoid circular refs
    )
    metrics_computed_at: datetime | None = Field(
        default=None,
        description="When metrics were last computed"
    )

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary information about this entity.

        Override in subclasses to add entity-specific summary fields.

        Returns:
            Dictionary with entity summary
        """
        summary: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
        }

        if self.created_at:
            summary["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            summary["updated_at"] = self.updated_at.isoformat()
        if self.metrics_computed_at:
            summary["metrics_computed_at"] = self.metrics_computed_at.isoformat()
            summary["has_computed_metrics"] = bool(self.computed_metrics)

        return summary
    
    def has_metric(self, metric_name: str) -> bool:
        """Check if a specific metric has been computed."""
        return metric_name in self.computed_metrics
    
    def get_metric(self, metric_name: str, default: Any = None) -> Any:
        """
        Get a computed metric value.
        
        Args:
            metric_name: Name of the metric
            default: Default value if metric not found
            
        Returns:
            Metric value or default
        """
        return self.computed_metrics.get(metric_name, default)
    
    def set_metric(self, metric_name: str, value: Any) -> None:
        """
        Set a computed metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        self.computed_metrics[metric_name] = value
        self.metrics_computed_at = datetime.now()
    
    def clear_metrics(self) -> None:
        """Clear all computed metrics."""
        self.computed_metrics.clear()
        self.metrics_computed_at = None

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"


class HierarchicalEntity(BaseEntity[TChild]):
    """
    Entity with parent-child hierarchy support.

    Used for spatial hierarchy (Room → Level → Building → Portfolio)
    and other hierarchical structures.

    Provides:
    - Parent reference (optional)
    - Child collection management
    - Helper methods for hierarchy navigation
    - Child counting
    """

    # Hierarchy
    parent_id: str | None = Field(
        default=None,
        description="Parent entity identifier"
    )

    child_ids: list[str] = Field(
        default_factory=list,
        description="IDs of child entities"
    )

    def add_child(self, child_id: str) -> None:
        """
        Add a child entity to this entity.

        Args:
            child_id: Child entity identifier to add
        """
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)

    def add_children(self, child_ids: list[str]) -> None:
        """
        Add multiple child entities.

        Args:
            child_ids: List of child entity identifiers to add
        """
        for child_id in child_ids:
            self.add_child(child_id)

    def remove_child(self, child_id: str) -> bool:
        """
        Remove a child entity from this entity.

        Args:
            child_id: Child entity identifier to remove

        Returns:
            True if child was removed, False if not found
        """
        if child_id in self.child_ids:
            self.child_ids.remove(child_id)
            return True
        return False

    def has_child(self, child_id: str) -> bool:
        """
        Check if entity contains a specific child.

        Args:
            child_id: Child entity identifier to check

        Returns:
            True if child exists, False otherwise
        """
        return child_id in self.child_ids

    @property
    def child_count(self) -> int:
        """Get number of child entities."""
        return len(self.child_ids)

    @property
    def has_children(self) -> bool:
        """Check if entity has any children."""
        return len(self.child_ids) > 0

    @property
    def is_empty(self) -> bool:
        """Check if entity has no children."""
        return len(self.child_ids) == 0

    def get_summary(self) -> dict[str, Any]:
        """Get summary including hierarchy information."""
        summary = super().get_summary()
        summary.update({
            "parent_id": self.parent_id,
            "child_count": self.child_count,
            "child_ids": self.child_ids,
        })
        return summary

    def compute_from_children(
        self,
        child_lookup: Callable[[str], "BaseEntity[Any] | None"]
    ) -> None:
        """
        Compute aggregated physical properties from children.

        This method aggregates:
        - area: sum of children's areas
        - volume: sum of children's volumes
        - occupancy: sum of children's occupancies
        - orientations: combined list of all unique orientations
        - window_areas: combined list of all window areas
        - shading_factors: combined list of all shading factors
        - glass_to_wall_ratio: computed from total window area / total wall area
        - last_renovation_year: most recent renovation year among children

        Args:
            child_lookup: Function to retrieve child entity by ID.
                         Should return None if child not found.
                         Child can be any BaseEntity (Room, Level, etc.)
        """
        if not self.child_ids:
            return

        # Initialize aggregation variables
        total_area = 0.0
        total_volume = 0.0
        total_occupancy = 0
        total_window_area = 0.0
        all_orientations: list[float] = []
        all_window_areas: list[float] = []
        all_shading_factors: list[float] = []
        most_recent_renovation: int | None = None
        
        children_with_area = 0
        children_with_volume = 0
        children_with_occupancy = 0

        # Aggregate from all children
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child is None:
                continue

            # Aggregate numerical values
            if child.area is not None:
                total_area += child.area
                children_with_area += 1

            if child.volume is not None:
                total_volume += child.volume
                children_with_volume += 1

            if child.occupancy is not None:
                total_occupancy += child.occupancy
                children_with_occupancy += 1

            # Aggregate lists
            if child.orientations:
                all_orientations.extend(child.orientations)

            if child.window_areas:
                all_window_areas.extend(child.window_areas)
                total_window_area += sum(child.window_areas)

            if child.shading_factors:
                all_shading_factors.extend(child.shading_factors)

            # Track most recent renovation
            if child.last_renovation_year is not None:
                if most_recent_renovation is None:
                    most_recent_renovation = child.last_renovation_year
                else:
                    most_recent_renovation = max(most_recent_renovation, child.last_renovation_year)

        # Set aggregated values (only if we have data from children)
        if children_with_area > 0:
            self.area = total_area

        if children_with_volume > 0:
            self.volume = total_volume

        if children_with_occupancy > 0:
            self.occupancy = total_occupancy

        if all_orientations:
            self.orientations = all_orientations

        if all_window_areas:
            self.window_areas = all_window_areas

        if all_shading_factors:
            self.shading_factors = all_shading_factors

        if most_recent_renovation is not None:
            self.last_renovation_year = most_recent_renovation

        # Compute glass-to-wall ratio if we have sufficient data
        if total_area > 0 and total_window_area > 0:
            # Estimate wall area (simplified - assumes external walls)
            # This is a rough estimate; actual calculation would need more geometric info
            self.glass_to_wall_ratio = min(total_window_area / total_area, 1.0)

    def get_aggregated_area(
        self,
        child_lookup: Callable[[str], "BaseEntity[Any] | None"]
    ) -> float:
        """
        Get total area by aggregating from children.

        Args:
            child_lookup: Function to retrieve child entity by ID

        Returns:
            Total area in m², or 0 if no children with area data
        """
        if self.area is not None:
            return self.area

        total = 0.0
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child and child.area is not None:
                total += child.area

        return total

    def get_aggregated_volume(
        self,
        child_lookup: Callable[[str], "BaseEntity[Any] | None"]
    ) -> float:
        """
        Get total volume by aggregating from children.

        Args:
            child_lookup: Function to retrieve child entity by ID

        Returns:
            Total volume in m³, or 0 if no children with volume data
        """
        if self.volume is not None:
            return self.volume

        total = 0.0
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child and child.volume is not None:
                total += child.volume

        return total

    def get_aggregated_occupancy(
        self,
        child_lookup: Callable[[str], "BaseEntity[Any] | None"]
    ) -> int:
        """
        Get total occupancy by aggregating from children.

        Args:
            child_lookup: Function to retrieve child entity by ID

        Returns:
            Total occupancy count, or 0 if no children with occupancy data
        """
        if self.occupancy is not None:
            return self.occupancy

        total = 0
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child and child.occupancy is not None:
                total += child.occupancy

        return total

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}(id={self.id}, name={self.name}, "
            f"children={self.child_count})"
        )
