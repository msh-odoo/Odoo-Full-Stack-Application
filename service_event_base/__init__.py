# -*- coding: utf-8 -*-
"""
Service Event Base Module - Main Initialization

This file is the entry point for the service_event_base module.

PYTHON PACKAGE STRUCTURE:
    Odoo treats each module as a Python package.
    The __init__.py file defines what gets imported when the module loads.

IMPORT ORDER MATTERS:
    1. Hooks first (needed by __manifest__.py declarations)
    2. Models next (register with ORM)
    3. Controllers last (if any - none in base module)

WHY THIS ORDER:
    - Hooks are referenced by name in __manifest__.py (must be importable)
    - Models must load before views reference them
    - Controllers depend on models being registered

WHY NOT IMPORT EVERYTHING:
    - Only import what's needed for module to function
    - Avoid circular dependencies
    - Keep namespace clean
    - Explicit imports = better debugging

ODOO MODULE LOADING SEQUENCE:
    1. Odoo scans __manifest__.py
    2. Odoo imports __init__.py (this file)
    3. Hooks are called (if declared in manifest)
    4. Models are registered with ORM
    5. Data files (XML) are loaded
    6. Module is marked as installed
"""

# Import hook functions to module level
# WHY: __manifest__.py references these by name (pre_init_hook, post_init_hook)
# Odoo looks for them as module attributes
from .hooks import pre_init_hook, post_init_hook

# Import models subpackage
# This will trigger models/__init__.py which imports all model files
from . import models
