#!/usr/bin/env python3
"""
Automated type error fixes for common patterns.
"""

import re
from pathlib import Path

def fix_aggregator_annotations(file_path: Path):
    """Fix missing type annotations in aggregators."""
    content = file_path.read_text()

    # Fix: all_test_ids = set()
    content = re.sub(
        r'all_test_ids = set\(\)',
        'all_test_ids: set[str] = set()',
        content
    )

    # Fix: all_params = set()
    content = re.sub(
        r'all_params = set\(\)',
        'all_params: set[str] = set()',
        content
    )

    # Fix: rec_counts = {}
    content = re.sub(
        r'rec_counts = \{\}',
        'rec_counts: dict[str, int] = {}',
        content
    )

    # Fix: issue_counts = {}
    content = re.sub(
        r'issue_counts = \{\}',
        'issue_counts: dict[str, int] = {}',
        content
    )

    file_path.write_text(content)
    print(f"✓ Fixed aggregator annotations in {file_path.name}")

def fix_chart_none_checks(file_path: Path):
    """Fix DataFrame None checks in charts."""
    content = file_path.read_text()

    # Find patterns like "if not df.empty:" and add None check
    # This is a simplified fix - manual review recommended
    lines = content.split('\n')
    modified = False

    for i, line in enumerate(lines):
        if 'if df.empty:' in line and 'df is not None' not in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + 'if df is not None and df.empty:'
            modified = True
        elif 'if not df.empty:' in line and 'df is not None' not in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + 'if df is not None and not df.empty:'
            modified = True

    if modified:
        file_path.write_text('\n'.join(lines))
        print(f"✓ Fixed None checks in {file_path.name}")

def add_type_ignores_for_complex_cases(file_path: Path):
    """Add type: ignore comments for complex cases that need manual review."""
    content = file_path.read_text()

    # Add type: ignore for pandas Any returns (temporary)
    if 'no-any-return' in str(file_path):
        content = re.sub(
            r'return \(([^)]+\.notna\(\)\.sum\(\)[^)]*)\)',
            r'return float(\1)  # type: ignore[no-any-return]',
            content
        )

    file_path.write_text(content)

# Main execution
if __name__ == '__main__':
    base_dir = Path('/Users/brunoadam/Documents/work/current/projects/ieq-analytics/analytics/clean')

    # Fix aggregators
    for agg_file in (base_dir / 'core' / 'analytics' / 'aggregators').glob('*.py'):
        if agg_file.name != '__init__.py':
            fix_aggregator_annotations(agg_file)

    # Fix charts
    for chart_file in (base_dir / 'core' / 'reporting' / 'charts').glob('*.py'):
        if chart_file.name != '__init__.py':
            fix_chart_none_checks(chart_file)

    print("\n✓ Automated fixes applied!")
    print("Note: Some complex cases may still need manual review.")
