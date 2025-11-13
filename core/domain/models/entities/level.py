"""Level domain entity."""

from datetime import datetime
from typing import Any, Callable

from pydantic import Field

from core.domain.models.base.base_entity import HierarchicalEntity


class Level(HierarchicalEntity[str]):
    """
    Level/floor entity representing a single floor in a building.

    Aggregates multiple rooms on the same floor level.
    Inherits hierarchy management (parent_id, child_ids) from HierarchicalEntity.
    - parent_id represents the building_id
    - child_ids represents the room_ids
    
    Physical properties (area, volume, occupancy, etc.) are computed from child rooms.
    Use compute_from_children() to aggregate values from rooms.
    """

    # Floor information
    floor_number: int = Field(..., description="Floor number (0=ground, negative=basement)")

    # Convenience properties for semantic clarity
    @property
    def building_id(self) -> str | None:
        """Get parent building ID (alias for parent_id)."""
        return self.parent_id

    @building_id.setter
    def building_id(self, value: str | None) -> None:
        """Set parent building ID (alias for parent_id)."""
        self.parent_id = value

    @property
    def room_ids(self) -> list[str]:
        """Get room IDs (alias for child_ids)."""
        return self.child_ids

    def add_room(self, room_id: str) -> None:
        """
        Add a room to this level.

        Args:
            room_id: Room identifier to add
        """
        self.add_child(room_id)

    def remove_room(self, room_id: str) -> bool:
        """
        Remove a room from this level.

        Args:
            room_id: Room identifier to remove

        Returns:
            True if room was removed, False if not found
        """
        return self.remove_child(room_id)

    def has_room(self, room_id: str) -> bool:
        """Check if level contains a specific room."""
        return self.has_child(room_id)

    @property
    def room_count(self) -> int:
        """Get number of rooms on this level."""
        return self.child_count

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this level."""
        # Get base summary from HierarchicalEntity
        summary = super().get_summary()
        
        # Add level-specific information
        summary.update({
            "building_id": self.building_id,
            "floor_number": self.floor_number,
            "room_count": self.room_count,
            "total_area_m2": self.area,  # Inherited from BaseEntity, computed from children
            "room_ids": self.room_ids,
        })
        
        return summary
    
    def compute_metrics(
        self,
        room_lookup: Callable[[str], Any] | None = None,
        force_recompute: bool = False
    ) -> dict[str, Any]:
        """
        Compute level-wide aggregated metrics from child rooms.
        
        Aggregates compliance metrics, TAIL ratings, and other metrics
        from all rooms on this level.
        
        Args:
            room_lookup: Function to retrieve Room objects by ID.
                        Required to aggregate from room metrics.
            force_recompute: If True, recompute even if metrics already cached
            
        Returns:
            Dictionary with aggregated metrics
            
        Example:
            level = Level(id="l1", name="Ground Floor", floor_number=0)
            level.add_room("room1")
            level.add_room("room2")
            
            # Compute metrics from rooms
            metrics = level.compute_metrics(room_lookup=lambda id: rooms_dict[id])
            
            # Access cached results
            print(level.get_metric('average_compliance_rate'))  # 85.5
            print(level.get_metric('tail_thermal_rating'))  # 2
        """
        # Return cached results if available and not forcing recompute
        if not force_recompute and self.has_metric('level_metrics'):
            return self.get_metric('level_metrics')
        
        results: dict[str, Any] = {
            'room_count': self.room_count,
            'floor_number': self.floor_number
        }
        
        # If no room lookup provided, can't aggregate
        if room_lookup is None or not self.room_ids:
            self.set_metric('level_metrics', results)
            return results
        
        # Aggregate metrics from rooms
        compliance_rates = []
        tail_ratings = []
        en16798_categories = []
        
        for room_id in self.room_ids:
            room = room_lookup(room_id)
            if room is None:
                continue
            
            # Collect compliance rates
            if room.has_metric('overall_compliance_rate'):
                compliance_rates.append(room.get_metric('overall_compliance_rate'))
            
            # Collect TAIL ratings
            if room.has_metric('tail_overall_rating'):
                tail_ratings.append(room.get_metric('tail_overall_rating'))
            
            # Collect EN16798 categories
            if room.has_metric('en16798_category'):
                en16798_categories.append(room.get_metric('en16798_category'))
        
        # Calculate averages
        if compliance_rates:
            results['average_compliance_rate'] = sum(compliance_rates) / len(compliance_rates)
            results['min_compliance_rate'] = min(compliance_rates)
            results['max_compliance_rate'] = max(compliance_rates)
            results['rooms_analyzed'] = len(compliance_rates)
        
        if tail_ratings:
            results['average_tail_rating'] = sum(tail_ratings) / len(tail_ratings)
            results['worst_tail_rating'] = max(tail_ratings)  # Higher is worse
            results['best_tail_rating'] = min(tail_ratings)  # Lower is better
        
        if en16798_categories:
            # Count category distribution
            category_counts: dict[str, int] = {}
            for cat in en16798_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            results['en16798_category_distribution'] = category_counts
        
        # Cache all results
        for key, value in results.items():
            self.set_metric(key, value)
        
        self.set_metric('level_metrics', results)
        self.metrics_computed_at = datetime.now()
        
        return results
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get cached level metrics.
        
        Returns:
            Dictionary of cached metrics or empty dict if not computed
        """
        return self.get_metric('level_metrics', {})

