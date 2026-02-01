# -*- coding: utf-8 -*-
# Service Event Base Module Manifest
#
# This manifest defines the core business logic module for the Service Event & Booking System.
#
# ARCHITECTURE DECISION:
#     - Separated into base module (this) and website module (service_event_website)
#     - Base module handles: models, business logic, security, ORM operations
#     - Website module handles: web pages, controllers, snippets, portal
#
# WHY THIS SEPARATION:
#     - Allows installation of core business logic without website dependency
#     - Enables reuse of business models in other contexts (mobile, API, POS, etc.)
#     - Follows Odoo's modular architecture pattern (e.g., sale vs sale_management)
#     - Cleaner dependency graph and easier maintenance
#
# WHY NOT SINGLE MODULE:
#     - Would violate separation of concerns
#     - Would force website dependency even for API-only use cases
#     - Would make testing more complex (harder to unit test models separately)
#
# HOOK DECLARATIONS:
#     - pre_init_hook: Runs BEFORE module installation (SQL-level preparation)
#     - post_init_hook: Runs AFTER module installation (data initialization via ORM)
#
#     These hooks are declared as strings matching function names in hooks.py.
#     Odoo will import and execute them at the appropriate lifecycle stage.

{
    'name': 'Service Event Base',
    'version': '19.0.1.6.0',
    'category': 'Services',
    'summary': 'Core business logic for service event management and booking system',
    'description': """
        Service Event Base Module
        ==========================

        This module provides the foundational business logic for managing service events and bookings.

        Core Features:
        --------------
        * Service/Event Management (catalog, pricing, categorization)
        * Booking/Registration System (state workflow, validation)
        * Multi-company support
        * Advanced ORM operations (computed fields, constraints, overrides)
        * Security framework (groups, access rights, record rules)

        Technical Highlights:
        ---------------------
        * Demonstrates Odoo ORM concepts (compute, related, constraints)
        * Implements proper lifecycle hooks (pre-init, post-init, init)
        * Uses sequences for auto-numbering
        * Includes SQL-level optimizations (indexes, views)
        * Multi-company aware with proper domain filtering

        Architecture:
        -------------
        This is the BASE module. It must NOT depend on 'website' or 'portal'.
        For web integration, install the companion module: service_event_website

        Dependencies:
        -------------
        * base: Core Odoo framework
        * mail: Activity tracking and messaging (used for booking notifications)
    """,

    'author': 'Odoo Full-Stack Development Team',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',

    # Dependencies - ONLY base and mail, NO website/portal
    'depends': [
        'base',
        'mail',  # For activity tracking, chatter, notifications
    ],

    # Always load these data files
    'data': [
        # Security must load first (groups before access rights)
        'security/service_event_security.xml',
        'security/ir.model.access.csv',

        # Data files
        'data/sequences.xml',
        'data/categories.xml',

        # Views
        'views/service_event_views.xml',
        'views/service_booking_views.xml',
        'views/menus.xml',
    ],

    # Demo data (only loaded with demo mode)
    'demo': [
        'demo/demo_data.xml',
    ],

    # Lifecycle hooks - executed during installation
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',

    # Module behavior flags
    'installable': True,
    'application': True,  # This is a standalone application

    # External dependencies (Python packages)
    'external_dependencies': {
        'python': [],  # No additional Python packages required
    },

    # Assets (JS/CSS) - base module has no web assets
    'assets': {},
}
