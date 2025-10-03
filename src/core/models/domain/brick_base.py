"""Brick Schema base classes for enhanced semantic modeling.

This module provides base classes that integrate Brick Schema ontology
with our domain models, enabling semantic interoperability and standardization.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from brickschema.namespaces import BRICK, RDF, RDFS
from brickschema import Graph
from rdflib import URIRef, Literal


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
    
    def to_brick_graph(self, graph: Optional[Graph] = None) -> Graph:
        """Export entity to a Brick Schema RDF graph.
        
        Args:
            graph: Optional existing graph to add to. If None, creates new graph.
            
        Returns:
            Brick Schema graph with this entity
        """
        if graph is None:
            graph = Graph()
            graph.bind("brick", BRICK)
        
        if not self.brick_uri:
            raise ValueError("brick_uri must be set to export to RDF")
        
        # Convert to URIRef
        subject_uri = URIRef(self.brick_uri)
        
        # Add type triple
        if self.brick_type:
            type_uri = self.get_brick_type_uri()
            if type_uri:
                graph.add((
                    subject_uri,
                    RDF.type,
                    URIRef(type_uri)
                ))
        
        # Add relationship triples
        for predicate, targets in self.brick_relationships.items():
            # Convert predicate to URI
            if predicate.startswith('http'):
                pred_uri = URIRef(predicate)
            elif ':' in predicate:
                prefix, local = predicate.split(':', 1)
                if prefix == 'brick':
                    pred_uri = BRICK[local]
                else:
                    pred_uri = URIRef(predicate)
            else:
                pred_uri = BRICK[predicate]
            
            # Add triples for each target
            for target in targets:
                graph.add((subject_uri, pred_uri, URIRef(target)))
        
        # Add metadata as literals
        for key, value in self.brick_metadata.items():
            if isinstance(value, (str, int, float, bool)):
                # Convert to valid URI for predicate
                pred_uri = BRICK[key] if not key.startswith('http') else URIRef(key)
                graph.add((subject_uri, pred_uri, Literal(value)))
            elif isinstance(value, dict):
                # Handle complex metadata (e.g., measurements with units)
                # Skip for now or convert to string
                continue
        
        return graph
    
    def to_brick_turtle(self) -> str:
        """Export entity as Turtle/TTL format.
        
        Returns:
            Turtle serialization of the entity
        """
        graph = self.to_brick_graph()
        return graph.serialize(format='turtle')
    
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


