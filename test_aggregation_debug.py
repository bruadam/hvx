#!/usr/bin/env python
"""Debug aggregation at all levels"""
from pathlib import Path
from connectors.csv import load_dummy_data
from core.entities import Portfolio
from core.enums import SpatialEntityType

data_root = Path(__file__).resolve().parent / "data" / "samples" / "dummy_data"
result = load_dummy_data(data_root)

# Build portfolio
if hasattr(result, "rooms"):
    rooms = result.rooms
    buildings = result.buildings
    floors = result.floors
    portfolio = result.portfolio or Portfolio(
        id="dummy_portfolio",
        name="Dummy Sample Portfolio",
        type=SpatialEntityType.PORTFOLIO,
    )
else:
    raise ValueError("Expected result with rooms attribute")

# Compute standards at all levels
print('Computing standards...')

# Create lookup functions
def room_lookup(room_id):
    return rooms.get(room_id)

def floor_lookup(floor_id):
    return floors.get(floor_id)

def building_lookup(building_id):
    return buildings.get(building_id)

# Compute room standards first
for room_id, room in rooms.items():
    room.compute_standards()

# Compute floor standards with room lookup
for floor_id, floor in floors.items():
    floor.compute_standards(room_lookup=room_lookup)

# Compute building standards with floor and room lookup
for building_id, building in buildings.items():
    building.compute_standards(floor_lookup=floor_lookup, room_lookup=room_lookup)

# Compute portfolio standards with building lookup
portfolio.compute_standards(building_lookup=building_lookup)

# Check a specific room (first room)
test_room = list(rooms.values())[0]
print(f'\n=== Room {test_room.id} ===')
room_results = test_room.computed_metrics.get('standards_results', {})
print(f'Standards results keys: {list(room_results.keys())}')
if 'en16798_1' in room_results:
    print(f'  EN16798: {room_results["en16798_1"].get("achieved_category", "n/a")}')
if 'tail' in room_results:
    print(f'  TAIL: {room_results["tail"].get("overall_rating_label", "n/a")}')

# Check floor (first floor)
test_floor = list(floors.values())[0]
print(f'\n=== Floor {test_floor.id} ===')
floor_results = test_floor.computed_metrics.get('floor_standards', {})
print(f'Floor standards keys: {list(floor_results.keys())}')
if 'en16798_1' in floor_results:
    print(f'  EN16798: {floor_results["en16798_1"].get("achieved_category", "n/a")}')
if 'tail' in floor_results:
    print(f'  TAIL: {floor_results["tail"].get("overall_rating_label", "n/a")}')

# Check building (first building)
test_building = list(buildings.values())[0]
print(f'\n=== Building {test_building.id} ===')
building_results = test_building.computed_metrics.get('building_standards', {})
print(f'Building standards keys: {list(building_results.keys())}')
if 'en16798_1' in building_results:
    print(f'  EN16798: {building_results["en16798_1"].get("achieved_category", "n/a")}')
if 'tail' in building_results:
    print(f'  TAIL: {building_results["tail"].get("overall_rating_label", "n/a")}')

# Check portfolio
print(f'\n=== Portfolio {portfolio.id} ===')
portfolio_results = portfolio.computed_metrics.get('portfolio_standards', {})
print(f'Portfolio standards keys: {list(portfolio_results.keys())}')
if 'en16798_1' in portfolio_results:
    print(f'  EN16798: {portfolio_results["en16798_1"].get("achieved_category", "n/a")}')
if 'tail' in portfolio_results:
    print(f'  TAIL: {portfolio_results["tail"].get("overall_rating_label", "n/a")}')
