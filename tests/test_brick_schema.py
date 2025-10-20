"""
Test Brick Schema integration in HVX data models.

This module tests the Brick Schema compatibility of domain and results models.
"""

import pytest
from datetime import datetime
from src.core.models.domain import Room, Level, Building, BrickSchemaEntity
from src.core.models.results import RoomAnalysis, LevelAnalysis, BuildingAnalysis, PortfolioAnalysis
from brickschema import Graph
from rdflib import URIRef


class TestBrickSchemaIntegration:
    """Test Brick Schema integration with domain models."""
    
    def test_room_brick_schema_basics(self):
        """Test Room model has Brick Schema support."""
        room = Room(
            id="room_101",
            name="Office 101",
            building_id="building_1"
        )
        
        assert room.brick_type == "brick:Room"
        assert room.brick_uri is not None
        assert "urn:building:building_1:room:room_101" in room.brick_uri
        
    def test_level_brick_schema_basics(self):
        """Test Level model has Brick Schema support."""
        level = Level(
            id="floor_1",
            name="First Floor",
            building_id="building_1",
            floor_number=1
        )
        
        assert level.brick_type == "brick:Floor"
        assert level.brick_uri is not None
        assert "urn:building:building_1:floor:floor_1" in level.brick_uri
        assert level.brick_metadata.get('floorNumber') == 1
    
    def test_building_brick_schema_basics(self):
        """Test Building model has Brick Schema support."""
        building = Building(
            id="building_1",
            name="Main Building",
            address="123 Main St",
            city="Copenhagen"
        )
        
        assert building.brick_type == "brick:Building"
        assert building.brick_uri == "urn:building:building_1"
        assert building.brick_metadata.get('address') == "123 Main St"
        assert building.brick_metadata.get('city') == "Copenhagen"
    
    def test_brick_relationships(self):
        """Test Brick Schema relationships are created correctly."""
        building = Building(id="building_1", name="Building 1")
        level = Level(id="floor_1", name="Floor 1", building_id="building_1")
        room = Room(id="room_101", name="Room 101", building_id="building_1", level_id="floor_1")
        
        # Add to hierarchy
        building.add_level(level)
        level.add_room(room)
        
        # Check relationships
        assert level.brick_uri in building.brick_relationships.get('hasPart', [])
        assert building.brick_uri in level.brick_relationships.get('isPartOf', [])
        assert room.brick_uri in level.brick_relationships.get('hasPart', [])
        assert level.brick_uri in room.brick_relationships.get('isPartOf', [])
    
    def test_room_analysis_brick_schema(self):
        """Test RoomAnalysis has Brick Schema support."""
        analysis = RoomAnalysis(
            room_id="room_101",
            room_name="Office 101",
            building_id="building_1",
            overall_compliance_rate=85.5
        )
        
        assert analysis.brick_type == "brick:Analysis_Result"
        assert analysis.brick_uri is not None
        assert "analysis" in analysis.brick_uri
        assert analysis.brick_metadata.get('complianceRate') == 85.5
    
    def test_level_analysis_brick_schema(self):
        """Test LevelAnalysis has Brick Schema support."""
        analysis = LevelAnalysis(
            level_id="floor_1",
            level_name="Floor 1",
            building_id="building_1",
            avg_compliance_rate=82.3
        )
        
        assert analysis.brick_type == "brick:Analysis_Result"
        assert analysis.brick_uri is not None
        assert analysis.brick_metadata.get('avgComplianceRate') == 82.3
    
    def test_building_analysis_brick_schema(self):
        """Test BuildingAnalysis has Brick Schema support."""
        analysis = BuildingAnalysis(
            building_id="building_1",
            building_name="Building 1",
            avg_compliance_rate=80.0
        )
        
        assert analysis.brick_type == "brick:Analysis_Result"
        assert analysis.brick_uri is not None
        assert analysis.brick_metadata.get('avgComplianceRate') == 80.0
    
    def test_portfolio_analysis_brick_schema(self):
        """Test PortfolioAnalysis has Brick Schema support."""
        analysis = PortfolioAnalysis(
            portfolio_name="My Portfolio",
            portfolio_id="portfolio_1",
            avg_compliance_rate=78.5
        )
        
        assert analysis.brick_type == "brick:Analysis_Result"
        assert analysis.brick_uri is not None
        assert "urn:portfolio:portfolio_1" in analysis.brick_uri
        assert analysis.brick_metadata.get('avgComplianceRate') == 78.5


class TestBrickSchemaExport:
    """Test Brick Schema RDF export functionality."""
    
    def test_to_brick_dict(self):
        """Test exporting entity to Brick Schema dictionary."""
        room = Room(
            id="room_101",
            name="Office 101",
            building_id="building_1"
        )
        
        brick_dict = room.to_brick_dict()
        
        assert '@id' in brick_dict
        assert '@type' in brick_dict
        assert brick_dict['@id'] == room.brick_uri
        # The type URI contains the Brick namespace
        assert 'Room' in brick_dict['@type']
    
    def test_to_brick_graph(self):
        """Test exporting entity to RDF graph."""
        room = Room(
            id="room_101",
            name="Office 101",
            building_id="building_1",
            area_m2=25.0
        )
        
        graph = room.to_brick_graph()
        
        # Check that graph contains triples
        assert len(graph) > 0
        
        # Check that the room URI is in the graph
        room_uri = URIRef(room.brick_uri)
        subjects = set(graph.subjects())
        assert room_uri in subjects
    
    def test_to_brick_turtle(self):
        """Test exporting entity to Turtle format."""
        building = Building(
            id="building_1",
            name="Main Building",
            address="123 Main St"
        )
        
        turtle = building.to_brick_turtle()
        
        # Check that Turtle contains expected elements
        assert 'brick:Building' in turtle
        assert building.brick_uri in turtle
        assert '@prefix brick:' in turtle
    
    def test_building_hierarchy_graph(self):
        """Test exporting full building hierarchy to RDF graph."""
        # Create hierarchy
        building = Building(id="building_1", name="Building 1")
        level = Level(id="floor_1", name="Floor 1", building_id="building_1")
        room1 = Room(id="room_101", name="Room 101", building_id="building_1")
        room2 = Room(id="room_102", name="Room 102", building_id="building_1")
        
        # Build hierarchy
        building.add_level(level)
        level.add_room(room1)
        level.add_room(room2)
        
        # Export to graph
        graph = Graph()
        graph.bind("brick", "https://brickschema.org/schema/Brick#")
        
        building.to_brick_graph(graph)
        level.to_brick_graph(graph)
        room1.to_brick_graph(graph)
        room2.to_brick_graph(graph)
        
        # Check graph has expected number of triples
        assert len(graph) > 10  # At least types and relationships
        
        # Serialize to Turtle and check structure
        turtle = graph.serialize(format='turtle')
        assert 'brick:Building' in turtle
        assert 'brick:Floor' in turtle
        assert 'brick:Room' in turtle
        assert 'brick:hasPart' in turtle
        assert 'brick:isPartOf' in turtle


class TestBackwardCompatibility:
    """Test that Brick Schema changes maintain backward compatibility."""
    
    def test_room_backward_compatibility(self):
        """Test Room model works without Brick Schema fields."""
        # Create room without specifying Brick Schema fields
        room = Room(
            id="room_101",
            name="Office 101",
            building_id="building_1",
            area_m2=25.0
        )
        
        # All original fields should work
        assert room.id == "room_101"
        assert room.name == "Office 101"
        assert room.building_id == "building_1"
        assert room.area_m2 == 25.0
        
        # Brick Schema fields are auto-populated
        assert room.brick_type is not None
        assert room.brick_uri is not None
    
    def test_building_backward_compatibility(self):
        """Test Building model works with original API."""
        building = Building(
            id="building_1",
            name="Main Building"
        )
        
        level = Level(
            id="floor_1",
            name="Floor 1",
            building_id="building_1"
        )
        
        room = Room(
            id="room_101",
            name="Room 101",
            building_id="building_1"
        )
        
        # Original methods should still work
        building.add_level(level)
        building.add_room(room, level_id="floor_1")
        
        assert building.get_level_count() == 1
        assert building.get_room_count() == 1
        assert building.get_level("floor_1") is not None
        assert building.get_room("room_101") is not None
    
    def test_analysis_backward_compatibility(self):
        """Test analysis models work with original API."""
        analysis = RoomAnalysis(
            room_id="room_101",
            room_name="Office 101",
            building_id="building_1"
        )
        
        # Original methods should work
        analysis.calculate_overall_metrics()
        
        # Can serialize to dict (for JSON export)
        data = analysis.model_dump()
        assert 'room_id' in data
        assert 'room_name' in data
        assert 'building_id' in data
        
        # Brick Schema fields are included but optional
        assert 'brick_type' in data
        assert 'brick_uri' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
