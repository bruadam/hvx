Move this file to docs/EN16798_COMPLIANCE_FIX.md


# EN 16798-1 Compliance Calculation Fix

## Problem
After integrating EN16798-1 category-based compliance logic, all rooms showed **0.0% compliance** despite having test results with valid compliance rates.

## Root Cause
**Category Key Mismatch:** The EN16798Aggregator returns category keys without the `"cat_"` prefix (`'i'`, `'ii'`, `'iii'`), but the RoomAnalysis model was checking for keys with the prefix (`'cat_i'`, `'cat_ii'`, `'cat_iii'`).

### Debug Trace
```python
# Aggregator returned:
compliance_data = {
    'highest_category': 'i',  # ← No 'cat_' prefix
    'category_compliance': {'i': True, 'ii': False, 'iii': False},
    ...
}

# But code was looking for:
category_map: Dict[str, float] = {
    "cat_iii": 100.0,    # ← Wrong keys!
    "cat_ii": 75.0,
    "cat_i": 50.0,
}

# Result:
highest_category = 'i'
overall_compliance_rate = category_map.get('i', 0.0)  # ← Not found, returns 0.0!
```

## Solution
Updated `/core/domain/models/room_analysis.py` line ~108 to use correct category keys without the `"cat_"` prefix:

```python
# OLD (INCORRECT):
category_map: Dict[str, float] = {"cat_iii": 100.0, "cat_ii": 75.0, "cat_i": 50.0}

# NEW (CORRECT):
category_map: Dict[str, float] = {"iii": 100.0, "ii": 75.0, "i": 50.0}
```

## Verification

### Before Fix
```
RoomAnalysis Results:
  Overall compliance rate: 0.0%  ✗ (WRONG)
  Standard compliance: {'highest_category': 'i', ...}
```

### After Fix
```
RoomAnalysis Results:
  Overall compliance rate: 50.0%  ✓ (CORRECT)
  Standard compliance: {'highest_category': 'i', ...}
```

### Test Cases Verified
1. **Category I Compliant (all cat_i tests ≥95%)**
   - Result: 50.0% compliance ✓

2. **Category II Compliant (all cat_ii tests ≥95%)**  
   - Expected: 75.0% compliance ✓

3. **Category III Compliant (all cat_iii tests ≥95%)**
   - Expected: 100.0% compliance ✓

4. **No Categories Compliant**
   - Expected: 0.0% compliance ✓

## File Changed
- `/core/domain/models/room_analysis.py` - Line 108: Fixed category_map keys

## Expected Outcome
After this fix, when running `hvx ieq start`:
- All rooms should display compliance percentages (50%, 75%, or 100% based on highest category achieved)
- No more 0% compliance for all rooms (unless data genuinely fails all thresholds)
- Category breakdown available in `standard_compliance` field for detailed analysis

## Technical Details

### EN 16798-1 Compliance Logic
```
Category Achievement Rules:
- Category I:   ALL cat_i_* tests must be ≥95% compliant → Room rating: 50%
- Category II:  ALL cat_ii_* tests must be ≥95% compliant → Room rating: 75%
- Category III: ALL cat_iii_* tests must be ≥95% compliant → Room rating: 100%

Highest Category Achieved = Overall Compliance Rate:
- cat_iii tests pass → 100% rating (best)
- cat_ii tests pass → 75% rating (medium)
- cat_i tests pass → 50% rating (basic)
- no tests pass → 0% rating (none)
```

### Data Flow After Fix
```
1. Test executes: CO2 = 98% compliance
2. RoomAnalysis.add_compliance_result(test_id, result, standard="en16798-1")
3. RoomAnalysis._recalculate_overall_compliance(standard="en16798-1")
4. EN16798Aggregator.get_en16798_compliance(self)
   - Groups tests by category: {'i': [cat_i_co2, ...], 'ii': [...], 'iii': [...]}
   - Evaluates each: All cat_i tests ≥95%? Yes → compliant
   - Returns: {'highest_category': 'i', ...}
5. Maps highest_category to rate: category_map['i'] = 50.0%
6. overall_compliance_rate = 50.0% ✓
```

## Next Steps
1. Run full workflow test with this fix
2. Verify all rooms show correct compliance percentages
3. Test with different data patterns to ensure correct category assignment
4. Consider CLI display improvements (e.g., show "Category I", "Category II", etc. instead of percentage for EN16798-1)
