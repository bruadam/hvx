#!/usr/bin/env python
"""
Brick Schema Integration Example for HVX

This example demonstrates how to use Brick Schema features in HVX:
1. Create building hierarchy with automatic Brick Schema metadata
2. Export to RDF/Turtle format
3. Query the data using SPARQL
4. Integrate with analysis results
"""

from src.core.models.domain import Room, Level, Building
from src.core.models.results import RoomAnalysis
from brickschema import Graph
from datetime import datetime


def main():
    print("=" * 80)
    print("Brick Schema Integration Example")
    print("=" * 80)
    
    # Step 1: Create a building hierarchy
    print("\n1. Creating Building Hierarchy with Brick Schema Support")
    print("-" * 80)
    
    building = Building(
        id="htk_building",
        name="HTK Copenhagen",
        address="Nørrebrogade 44",
        city="Copenhagen",
        postal_code="2200",
        country="Denmark",
        construction_year=1920,
        total_area_m2=1500.0
    )
    
    # Create levels
    ground_floor = Level(
        id="ground",
        name="Ground Floor",
        building_id="htk_building",
        floor_number=0
    )
    
    first_floor = Level(
        id="first",
        name="First Floor",
        building_id="htk_building",
        floor_number=1
    )
    
    # Create rooms
    office_101 = Room(
        id="101",
        name="Office 101",
        building_id="htk_building",
        level_id="ground",
        area_m2=25.0,
        volume_m3=75.0,
        capacity_people=4
    )
    
    office_102 = Room(
        id="102",
        name="Meeting Room",
        building_id="htk_building",
        level_id="ground",
        area_m2=35.0,
        volume_m3=105.0,
        capacity_people=8
    )
    
    office_201 = Room(
        id="201",
        name="Open Office",
        building_id="htk_building",
        level_id="first",
        area_m2=120.0,
        volume_m3=360.0,
        capacity_people=20
    )
    
    # Build hierarchy
    building.add_level(ground_floor)
    building.add_level(first_floor)
    ground_floor.add_room(office_101)
    ground_floor.add_room(office_102)
    first_floor.add_room(office_201)
    
    print(f"✓ Created building: {building.name}")
    print(f"  - Brick Type: {building.brick_type}")
    print(f"  - Brick URI: {building.brick_uri}")
    print(f"  - Levels: {len(building.levels)}")
    print(f"  - Total Rooms: {building.get_room_count()}")
    
    # Step 2: Display Brick Schema relationships
    print("\n2. Brick Schema Relationships")
    print("-" * 80)
    
    print(f"\nBuilding relationships:")
    for pred, targets in building.brick_relationships.items():
        print(f"  {pred}:")
        for target in targets:
            print(f"    → {target}")
    
    print(f"\nGround Floor relationships:")
    for pred, targets in ground_floor.brick_relationships.items():
        print(f"  {pred}:")
        for target in targets:
            print(f"    → {target}")
    
    print(f"\nOffice 101 relationships:")
    for pred, targets in office_101.brick_relationships.items():
        print(f"  {pred}:")
        for target in targets:
            print(f"    → {target}")
    
    # Step 3: Export to RDF Graph
    print("\n3. Exporting to RDF Graph")
    print("-" * 80)
    
    graph = Graph()
    graph.bind("brick", "https://brickschema.org/schema/Brick#")
    
    # Export all entities
    building.to_brick_graph(graph)
    for level in building.levels:
        level.to_brick_graph(graph)
        for room in level.rooms:
            room.to_brick_graph(graph)
    
    print(f"✓ Created RDF graph with {len(graph)} triples")
    
    # Step 4: Export to Turtle format
    print("\n4. Turtle Format Export")
    print("-" * 80)
    
    turtle = graph.serialize(format='turtle')
    print("First 1000 characters of Turtle output:")
    print(turtle[:1000])
    print("...")
    
    # Save to file
    output_file = "/tmp/htk_building_brick.ttl"
    with open(output_file, 'w') as f:
        f.write(turtle)
    print(f"\n✓ Saved full Turtle export to: {output_file}")
    
    # Step 5: SPARQL Query Example
    print("\n5. SPARQL Query Example")
    print("-" * 80)
    
    # Query all rooms and their areas
    query = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    
    SELECT ?room ?area WHERE {
        ?room a brick:Room .
        OPTIONAL { ?room brick:area ?area }
    }
    """
    
    print("Query: Find all rooms")
    results = graph.query(query)
    print(f"Found {len(results)} rooms:")
    for row in results:
        room_uri = str(row.room)
        # area = row.area if row.area else "N/A"
        print(f"  - {room_uri}")
    
    # Step 6: Add Analysis Results
    print("\n6. Integrating with Analysis Results")
    print("-" * 80)
    
    analysis = RoomAnalysis(
        room_id="101",
        room_name="Office 101",
        building_id="htk_building",
        level_id="ground",
        overall_compliance_rate=87.5,
        overall_quality_score=92.0,
        analysis_timestamp=datetime.now()
    )
    
    print(f"✓ Created analysis for {analysis.room_name}")
    print(f"  - Brick Type: {analysis.brick_type}")
    print(f"  - Brick URI: {analysis.brick_uri}")
    print(f"  - Compliance Rate: {analysis.overall_compliance_rate}%")
    print(f"  - Quality Score: {analysis.overall_quality_score}%")
    
    # Link analysis to room
    office_101.add_brick_relationship("hasAnalysis", analysis.brick_uri)
    
    # Add analysis to graph
    analysis.to_brick_graph(graph)
    
    print(f"\n✓ Updated RDF graph (now has {len(graph)} triples)")
    
    # Step 7: Export combined data
    print("\n7. Export Combined Building + Analysis Data")
    print("-" * 80)
    
    combined_turtle = graph.serialize(format='turtle')
    combined_file = "/tmp/htk_building_with_analysis.ttl"
    with open(combined_file, 'w') as f:
        f.write(combined_turtle)
    
    print(f"✓ Saved combined data to: {combined_file}")
    print(f"  Total triples: {len(graph)}")
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"""
    ✅ Successfully demonstrated Brick Schema integration in HVX:
    
    1. Created building hierarchy with {building.get_room_count()} rooms across {len(building.levels)} floors
    2. Automatic Brick Schema URIs and types for all entities
    3. Hierarchical relationships (hasPart, isPartOf) automatically created
    4. Exported to RDF graph with {len(graph)} triples
    5. Saved to Turtle format files:
       - {output_file}
       - {combined_file}
    6. Demonstrated SPARQL queries on the data
    7. Integrated analysis results with Brick Schema metadata
    
    All data is now interoperable with the Brick Schema ecosystem!
    """)


if __name__ == "__main__":
    main()
