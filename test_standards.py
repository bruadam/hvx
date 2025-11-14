#!/usr/bin/env python
"""Test standards computation"""

from pathlib import Path
from connectors.csv import load_dummy_data

data_root = Path('data/samples/dummy_data')
result = load_dummy_data(data_root)

if hasattr(result, 'rooms'):
    rooms = result.rooms
    room = list(rooms.values())[0]
    print(f'Room: {room.name}')
    print(f'Available metrics: {room.available_metrics}')
    print(f'Has data: {room.has_data}')
    print()
    
    # Test standards computation
    from core.standards_registry import get_registry
    registry = get_registry()
    
    applicable = registry.get_applicable_standards(
        country='DK',
        building_type='office',
        available_metrics=set(room.available_metrics),
    )
    print(f'Applicable standards: {[s.id for s in applicable]}')
    print()
    
    # Try to run compute_standards
    print('Running compute_standards...')
    result = room.compute_standards(country='DK', building_type='office', force_recompute=True)
    print(f'Result keys: {list(result.keys())}')
    for key, value in result.items():
        if isinstance(value, dict):
            print(f'  {key}: {list(value.keys())[:5]}')
        else:
            print(f'  {key}: {value}')
