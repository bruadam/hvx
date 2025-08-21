"""
HTK (Høje-Taastrup Kommune) Report Template Package

This package contains the complete HTK report template implementation,
including chart generation and HTML template rendering.
"""

from .htk_template import HTKReportTemplate, create_htk_template

__all__ = ['HTKReportTemplate', 'create_htk_template']
