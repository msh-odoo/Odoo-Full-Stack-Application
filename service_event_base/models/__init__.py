# -*- coding: utf-8 -*-
"""
Service Event Base Models Package

This package contains all model definitions for the service_event_base module.

MODEL REGISTRATION:
    Odoo automatically discovers and registers models when they are imported.
    Each model class inherits from models.Model and is registered in the ORM.

IMPORT PATTERN:
    - Import model files in logical dependency order
    - Base/parent models first, dependent models later
    - If models reference each other, import order doesn't matter
      (Odoo resolves forward references)

WHY SEPARATE FILES:
    - Each model in its own file (maintainability)
    - Easier code review and git diffs
    - Follows Odoo standard practice
    - Enables parallel development on different models

WHY THIS STRUCTURE:
    models/
        __init__.py (this file)
        service_event.py (core service/event model)
        service_event_category.py (master data)
        service_event_tag.py (master data)
        service_booking.py (transaction model)

FILE NAMING CONVENTION:
    - Lowercase with underscores
    - Matches model _name (e.g., service.event → service_event.py)
    - Singular form (event not events, booking not bookings)
"""

# Master data models (no dependencies)
from . import service_event_category
from . import service_event_tag

# Core business models
from . import service_event

# Transaction models (depend on core models)
from . import service_booking
