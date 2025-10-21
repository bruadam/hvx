#!/usr/bin/env python3
"""
Script to find unused classes in the src directory.
Analyzes Python files to identify classes that are defined but never imported or used.
"""

import ast
import os
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict


class ClassDefinitionVisitor(ast.NodeVisitor):
    """Visitor to find class definitions in a Python file."""

    def __init__(self):
        self.classes: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.add(node.name)
        self.generic_visit(node)


class ClassUsageVisitor(ast.NodeVisitor):
    """Visitor to find class usage (imports and references) in a Python file."""

    def __init__(self):
        self.used_classes: Set[str] = set()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.used_classes.add(alias.name.split('.')[-1])
            if alias.asname:
                self.used_classes.add(alias.asname)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.used_classes.add(alias.name)
            if alias.asname:
                self.used_classes.add(alias.asname)

    def visit_Name(self, node: ast.Name):
        self.used_classes.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.used_classes.add(node.attr)
        self.generic_visit(node)


def parse_file(file_path: Path) -> Tuple[Set[str], Set[str]]:
    """
    Parse a Python file to extract defined classes and used class names.

    Returns:
        Tuple of (defined_classes, used_classes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        # Find class definitions
        def_visitor = ClassDefinitionVisitor()
        def_visitor.visit(tree)

        # Find class usage
        usage_visitor = ClassUsageVisitor()
        usage_visitor.visit(tree)

        return def_visitor.classes, usage_visitor.used_classes

    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return set(), set()


def find_python_files(src_dir: Path) -> List[Path]:
    """Find all Python files in the src directory."""
    python_files = []
    for root, dirs, files in os.walk(src_dir):
        # Skip __pycache__ and .pytest_cache directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', '.git', 'venv', 'env']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    return python_files


def analyze_unused_classes(src_dir: Path) -> Dict[str, Set[str]]:
    """
    Analyze the src directory to find unused classes.
    A class is considered unused if it's never imported or used outside its defining file.

    Returns:
        Dictionary mapping file paths to sets of unused class names
    """
    python_files = find_python_files(src_dir)

    # Map of file -> defined classes
    file_definitions: Dict[Path, Set[str]] = {}

    # Map of file -> used classes
    file_usages: Dict[Path, Set[str]] = {}

    # Parse all files
    for file_path in python_files:
        defined, used = parse_file(file_path)
        file_definitions[file_path] = defined
        file_usages[file_path] = used

    # Find unused classes
    unused_classes: Dict[str, Set[str]] = {}

    for def_file_path, defined_classes in file_definitions.items():
        # Check if any class is used in OTHER files
        external_usage: Set[str] = set()

        for usage_file_path, used_classes in file_usages.items():
            # Skip the file where the class is defined
            if usage_file_path != def_file_path:
                external_usage.update(used_classes & defined_classes)

        # Classes that are defined but never used outside their own file
        unused = defined_classes - external_usage

        if unused:
            # Make path relative to src_dir for cleaner output
            relative_path = def_file_path.relative_to(src_dir.parent)
            unused_classes[str(relative_path)] = unused

    return unused_classes


def main():
    """Main entry point."""
    # Get the src directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / 'src'

    if not src_dir.exists():
        print(f"Error: src directory not found at {src_dir}")
        return

    print(f"Analyzing Python files in {src_dir}...\n")

    unused_classes = analyze_unused_classes(src_dir)

    if not unused_classes:
        print("✓ No unused classes found!")
        return

    print("Classes never used outside their defining file:\n")
    print("=" * 80)

    total_unused = 0
    for file_path in sorted(unused_classes.keys()):
        classes = sorted(unused_classes[file_path])
        total_unused += len(classes)
        print(f"\n{file_path}")
        for class_name in classes:
            print(f"  - {class_name}")

    print("\n" + "=" * 80)
    print(f"\nTotal: {total_unused} unused class(es) in {len(unused_classes)} file(s)")


if __name__ == '__main__':
    main()
