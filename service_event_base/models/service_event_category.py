# -*- coding: utf-8 -*-
"""
Service Event Category Model

PURPOSE:
    Master data model for categorizing services and events.
    Provides hierarchical organization and filtering capability.

BUSINESS RATIONALE:
    - Services need logical grouping (workshops, conferences, webinars)
    - Categories enable filtered browsing on website
    - Hierarchical structure allows sub-categories (e.g., Tech Workshops)
    - Used in snippet options for dynamic filtering

ORM CONCEPTS DEMONSTRATED:
    - Init method (_auto_init override)
    - SQL indexes for performance
    - Translatable fields
    - Hierarchical parent/child relationships

WHY THIS IS A SEPARATE MODEL:
    - Categories are master data (low change frequency)
    - Reusable across many services
    - Can be managed independently by administrators
    - Enables reporting and analytics by category

ALTERNATIVES NOT USED:
    - Selection field: Not flexible, hard-coded values, no hierarchy
    - Tags: Categories are exclusive (one per service), tags are inclusive
    - Free text: No consistency, no filtering capability
"""

from odoo import models, fields, api, _
from odoo.tools import SQL


class ServiceEventCategory(models.Model):
    """
    Category master data for service events.

    TECHNICAL CHARACTERISTICS:
        - Simple master data model
        - Supports hierarchy (parent/child)
        - Translatable name and description
        - Indexed for fast filtering

    MODEL INHERITANCE:
        Inherits from models.Model (standard persistent model)

    ORM REGISTRATION:
        Odoo automatically creates table: service_event_category
        Table name derived from _name with dots → underscores
    """

    _name = 'service.event.category'
    _description = 'Service Event Category'

    # ========================================================================
    # MAGIC FIELDS
    # ========================================================================
    # Odoo automatically creates 5 magic fields (don't define them):
    #   1. id: Integer primary key (auto-increment)
    #   2. create_date: Timestamp when record was created
    #   3. create_uid: Many2one to res.users (who created)
    #   4. write_date: Timestamp when record was last modified
    #   5. write_uid: Many2one to res.users (who last modified)
    #
    # WHY AUTOMATIC:
    #   - Every Odoo model needs tracking (auditing, sync, caching)
    #   - Reduces boilerplate code
    #   - Ensures consistency across all models
    #
    # ACCESS:
    #   record.id, record.create_date, etc.

    # ========================================================================
    # BASIC FIELDS
    # ========================================================================

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,  # Enable multi-language support
        help='Name of the service category (e.g., Workshop, Conference)',
    )
    # WHY TRANSLATE=TRUE:
    #   - Website may be multi-lingual
    #   - Category names should display in user's language
    #   - Odoo manages translations automatically (ir.translation table)

    code = fields.Char(
        string='Category Code',
        required=True,
        help='Unique technical identifier (e.g., WORKSHOP, WEBINAR)',
    )
    # WHY CODE FIELD:
    #   - Technical reference (doesn't change with translations)
    #   - Used in post_init_hook for idempotent category creation
    #   - Easier to reference in code than database IDs

    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of this category',
    )

    # ========================================================================
    # HIERARCHICAL FIELDS (Parent/Child Relationship)
    # ========================================================================

    parent_id = fields.Many2one(
        comodel_name='service.event.category',
        string='Parent Category',
        ondelete='cascade',
        help='Parent category for hierarchical organization',
    )
    # WHY SELF-REFERENTIAL:
    #   - Allows tree structure (Category → Sub-category)
    #   - Example: "Events" → "Workshops" → "Tech Workshops"
    #
    # WHY ondelete='cascade':
    #   - If parent deleted, children should also be deleted
    #   - Alternative: 'restrict' (prevent deletion if has children)
    #   - Alternative: 'set null' (orphan the children)

    child_ids = fields.One2many(
        comodel_name='service.event.category',
        inverse_name='parent_id',
        string='Sub-categories',
        help='Child categories under this category',
    )
    # WHY One2many:
    #   - Automatically computed inverse of parent_id
    #   - Enables tree view and hierarchical navigation

    # ========================================================================
    # ACTIVE FIELD (Archive/Unarchive Pattern)
    # ========================================================================

    active = fields.Boolean(
        default=True,
        help='Uncheck to archive the category without deleting it',
    )
    # ROLE OF ACTIVE FIELD:
    #   - Enables soft delete (archive instead of hard delete)
    #   - Records with active=False are hidden by default
    #   - Can be restored by setting active=True
    #
    # WHY USE ACTIVE:
    #   - Preserves historical data (bookings reference old categories)
    #   - Prevents accidental data loss
    #   - Odoo automatically filters active=True in searches
    #
    # HOW ODOO USES IT:
    #   - Default domain in search(): [('active', '=', True)]
    #   - Can show archived: search([]) or search([('active', 'in', [True, False])])
    #   - UI has "Archive" action automatically

    # ========================================================================
    # DISPLAY NAME AND RECORD NAME
    # ========================================================================

    _rec_name = 'name'
    # ROLE OF _rec_name:
    #   - Tells Odoo which field to use for display_name
    #   - Default is 'name' (can be overridden)
    #   - Used in Many2one widgets, breadcrumbs, logs
    #
    # DISPLAY_NAME:
    #   - Magical computed field (always available)
    #   - Defaults to value of _rec_name field
    #   - Can be customized via _compute_display_name()
    #
    # WHY NOT OVERRIDE HERE:
    #   - Simple models use name directly
    #   - Complex models might compute: "Code - Name (Parent)"

    # ========================================================================
    # SQL CONSTRAINTS
    # ========================================================================
    # NOTE: _sql_constraints shows deprecation warning in Odoo 19
    #       but new Constraint API is not yet available
    #       This is safe to use - will be updated when API is stable

    _sql_constraints = [
        (
            'unique_category_code',
            'UNIQUE(code)',
            'Category code must be unique!'
        ),
    ]
    # WHY SQL CONSTRAINT:
    #   - Enforced at database level (faster, more reliable)
    #   - Prevents race conditions (simultaneous creates)
    #   - Works even if bypassing ORM
    #
    # WHY NOT PYTHON CONSTRAINT:
    #   - Python runs after data is prepared (can still have race condition)
    #   - SQL is the last line of defense
    #
    # WHEN TO USE BOTH:
    #   - SQL for data integrity
    #   - Python for user-friendly error messages

    # ========================================================================
    # INIT METHOD (Database Optimization)
    # ========================================================================

    def _auto_init(self):
        """
        Initialize database table with indexes.

        PURPOSE:
            Called when model is first loaded or upgraded.
            Used to create/update database schema beyond basic fields.

        EXECUTION TIMING:
            - Runs after table creation
            - Runs on every module upgrade
            - Must be idempotent (safe to run multiple times)

        USE CASES:
            - Create database indexes (performance)
            - Create materialized views
            - Add check constraints
            - Modify column properties

        WHY OVERRIDE _auto_init:
            - Indexes are not declaratively defined in field definitions
            - Need SQL-level control over database structure
            - Performance optimization for frequent queries

        WHY NOT pre_init_hook:
            - pre_init runs before table exists
            - _auto_init runs after table creation (safe to add indexes)

        ODOO PATTERN:
            Always call super()._auto_init() first to ensure table exists.
        """

        # Call parent to ensure table and columns exist
        result = super()._auto_init()

        # Create index on 'code' for fast lookups
        # WHY INDEX ON CODE:
        #   - post_init_hook searches by code
        #   - Snippet options filter by code
        #   - Without index: full table scan (slow)
        #   - With index: O(log n) lookup (fast)
        self.env.cr.execute(SQL(
            """
            CREATE INDEX IF NOT EXISTS service_event_category_code_index
            ON service_event_category (code)
            WHERE active = true
            """
        ))
        # WHY PARTIAL INDEX (WHERE active = true):
        #   - Most queries only care about active categories
        #   - Partial index is smaller (faster, less disk space)
        #   - Archived categories rarely accessed

        # Create index on parent_id for hierarchy traversal
        # WHY INDEX ON parent_id:
        #   - Tree views need fast child lookups
        #   - Recursive queries benefit from index
        self.env.cr.execute(SQL(
            """
            CREATE INDEX IF NOT EXISTS service_event_category_parent_id_index
            ON service_event_category (parent_id)
            WHERE parent_id IS NOT NULL
            """
        ))

        return result
