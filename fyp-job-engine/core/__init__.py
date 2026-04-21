# AI Job Search & Resume Tailoring Engine - Core Module
"""
This module contains core infrastructure components including
database management and cost tracking utilities.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

from .database import Database
from .cost_tracker import CostTracker

__all__ = ['Database', 'CostTracker']
