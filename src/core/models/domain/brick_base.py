"""Brick Schema base classes for enhanced semantic modeling.

This module provides base classes that integrate Brick Schema ontology
with our domain models, enabling semantic interoperability and standardization.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from brickschema.namespaces import BRICK


class BrickSchemaEntity(BaseModel):
    """Base class for entities compatible with Brick Schema ontology.
    
    This class provides common attributes and methods for entities that
    map to Brick Schema concepts, enabling semantic web integration while
    maintaining analytical capabilities.
    """
    
    # Brick Schema metadata
    brick_type: Optional[str] = Field(
        None, 
        description="Brick Schema class URI (e.g., 'brick:Room', 'brick:Building')"
    )
    brick_uri: Optional[str] = Field(
        None,
        description="Unique RDF URI for this entity in Brick Schema format"
    )
    brick_relationships: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Brick Schema relationships (e.g., 'hasPart', 'isPartOf', 'feeds')"
    )
    brick_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional Brick Schema metadata and properties"
    )
    
    def get_brick_type_uri(self) -> Optional[str]:
        """Get the full Brick Schema type URI."""
        if self.brick_type:
            if self.brick_type.startswith('http'):
                return self.brick_type
            # Convert short form like 'brick:Room' to full URI
            if ':' in self.brick_type:
                prefix, local = self.brick_type.split(':', 1)
                if prefix == 'brick':
                    return str(BRICK[local])
            return str(BRICK[self.brick_type])
        return None
    
    def set_brick_type(self, brick_class: str) -> None:
        """Set the Brick Schema type for this entity.
        
        Args:
            brick_class: Brick Schema class name (e.g., 'Room', 'Building')
                        or full URI
        """
        self.brick_type = brick_class
    
    def add_brick_relationship(self, predicate: str, target_uri: str) -> None:
        """Add a Brick Schema relationship.
        
        Args:
            predicate: Relationship type (e.g., 'hasPart', 'isPartOf', 'feeds')
            target_uri: URI of the target entity
        """
        if predicate not in self.brick_relationships:
            self.brick_relationships[predicate] = []
        if target_uri not in self.brick_relationships[predicate]:
            self.brick_relationships[predicate].append(target_uri)
    
    def get_brick_relationships(self, predicate: Optional[str] = None) -> Dict[str, List[str]]:
        """Get Brick Schema relationships.
        
        Args:
            predicate: Optional relationship type to filter by
            
        Returns:
            Dictionary of relationships, or filtered list
        """
        if predicate:
            return {predicate: self.brick_relationships.get(predicate, [])}
        return self.brick_relationships
    
    def to_brick_dict(self) -> Dict[str, Any]:
        """Export entity as Brick Schema-compatible dictionary.
        
        Returns:
            Dictionary with Brick Schema metadata
        """
        brick_data = {
            '@id': self.brick_uri,
            '@type': self.get_brick_type_uri(),
            'relationships': self.brick_relationships,
        }
        
        # Add custom metadata
        if self.brick_metadata:
            brick_data.update(self.brick_metadata)
            
        return brick_data
    
    def validate_brick_schema(self) -> bool:
        """Validate that the entity conforms to Brick Schema.
        
        Returns:
            True if valid, raises exception otherwise
        """
        # Basic validation
        if self.brick_type and not self.brick_uri:
            raise ValueError("brick_uri must be set when brick_type is specified")
        
        return True


class BrickSchemaSpace(BrickSchemaEntity):
    """Base class for Brick Schema Space entities (Room, Floor, Building)."""
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-set brick type if not provided
        if not self.brick_type and hasattr(self, '_default_brick_type'):
            self.brick_type = self._default_brick_type


class BrickSchemaPoint(BrickSchemaEntity):
    """Base class for Brick Schema Point entities (sensors, setpoints)."""
    
    point_type: Optional[str] = Field(
        None,
        description="Brick Schema point type (e.g., 'Temperature_Sensor', 'CO2_Sensor')"
    )
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement (e.g., 'celsius', 'ppm')"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-set brick type for points
        if not self.brick_type and self.point_type:
            self.brick_type = f"brick:{self.point_type}"
