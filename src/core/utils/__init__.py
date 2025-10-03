"""Utility modules.

Note: Utilities have been reorganized:
- config_loader -> src.core.analytics.config_loader
- mapping -> src.core.parsers.mapping
- analysis_explorer -> src.cli.ui.explorers.analysis_explorer
- data_explorer -> src.cli.ui.explorers.data_explorer
- interactive_workflow -> src.cli.ui.workflows.interactive_workflow
- simplified_workflow -> src.cli.ui.workflows.simplified_workflow
"""

# Backward compatibility imports
from src.core.analytics.config_loader import *
from src.core.parsers.mapping import *

__all__ = [
    # 'ParameterMapping',
    # 'create_parameter_mapping',
]
