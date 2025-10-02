# IEQ Analytics Architecture Migration Plan

## Current Structure Issues

1. **Duplicate Analytics Code**: `analytics.py`, `climate_analytics.py`, `unified_analytics.py`
2. **Old Chart System**: `reporting/charts/` with scattered implementations
3. **Duplicate Services**: Old `report_engine.py` vs new `services/report_service.py`
4. **Unused Modules**: Several AI/ML features not currently used

## New Architecture

```
ieq_analytics/
├── core/                          # Core analytics engine
│   ├── __init__.py
│   ├── analytics_engine.py        # Unified analytics (from unified_analytics.py)
│   ├── rule_evaluator.py          # Rule evaluation logic
│   ├── filters.py                 # Time/period filtering
│   └── validators.py              # Data validation
│
├── graphs/                        # Graph library (already created)
│   ├── __init__.py
│   ├── registry.yaml
│   ├── renderers/                 # Chart rendering modules
│   │   ├── __init__.py
│   │   ├── bar_charts.py
│   │   ├── line_charts.py
│   │   ├── heatmaps.py
│   │   └── compliance_charts.py
│   └── fixtures/                  # Dummy data
│
├── services/                      # Service layer (already created)
│   ├── graph_service.py
│   ├── template_service.py
│   ├── analytics_service.py
│   └── report_service.py
│
├── cli/                           # CLI (already created)
│   ├── main.py
│   └── commands/
│
├── models/                        # Data models
│   ├── __init__.py
│   ├── analysis_result.py
│   └── enums.py                   # Move from root
│
└── utils/                         # Utilities
    ├── __init__.py
    └── mapping.py                 # Move from root
```

## Migration Steps

### Phase 1: Consolidate Analytics (PRIORITY)
- [x] Move `unified_analytics.py` → `core/analytics_engine.py`
- [ ] Extract filters → `core/filters.py`
- [ ] Extract rules → `core/rule_evaluator.py`
- [ ] Archive old `analytics.py`, `climate_analytics.py`

### Phase 2: Consolidate Models
- [ ] Move `enums.py` → `models/enums.py`
- [ ] Move `models.py` → `models/`
- [ ] Move `mapping.py` → `utils/mapping.py`

### Phase 3: Migrate Charts to New System
- [ ] Add existing charts to `graphs/registry.yaml`
- [ ] Migrate chart implementations to `graphs/renderers/`
- [ ] Update GraphService to use migrated charts
- [ ] Archive old `reporting/charts/`

### Phase 4: Clean Up Reporting
- [ ] Keep HTK template as reference
- [ ] Archive old `report_engine.py`, `graph_engine.py`
- [ ] Update services to handle all report generation

### Phase 5: Final Cleanup
- [ ] Remove unused AI/predictive modules
- [ ] Update all imports
- [ ] Update tests
- [ ] Update documentation

## Files to Archive

These will be moved to `_archived/` directory:

- `analytics.py` (superseded by core/analytics_engine.py)
- `climate_analytics.py` (functionality merged)
- `ventilation_rate_predictor.py` (not currently used)
- `reporting/ai_graph_analyzer.py` (not currently used)
- `reporting/graph_engine.py` (superseded by services)
- `reporting/report_engine.py` (superseded by services)
- `reporting/data_processor.py` (functionality in services)
- `reporting/pdf_generator.py` (functionality in services)
- `reporting/charts/manager.py` (superseded by GraphService)
- `reporting/charts/template_integration.py` (not needed)

## Files to Keep/Update

- `unified_analytics.py` → move to `core/analytics_engine.py`
- `models.py`, `enums.py` → reorganize in `models/`
- `mapping.py` → move to `utils/`
- HTK template → keep as working example
- All chart implementations → migrate to `graphs/renderers/`
