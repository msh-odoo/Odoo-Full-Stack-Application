# -*- coding: utf-8 -*-
"""
Service Event Tag Model

PURPOSE:
    Master data model for tagging services with multiple labels.
    Enables flexible, non-hierarchical classification.

BUSINESS RATIONALE:
    - Services can have multiple characteristics (Popular, New, Premium)
    - Tags are inclusive (service can have many tags)
    - Categories are exclusive (service has one category)
    - Used for filtering, visual indicators, marketing

ORM CONCEPTS DEMONSTRATED:
    - Many2many relationships (service ↔ tags)
    - Color field (for UI badges)
    - No hierarchy (flat structure vs categories)

DIFFERENCE FROM CATEGORY:
    - Category: One per service, hierarchical, structural
    - Tag: Many per service, flat, descriptive

    Example:
        Category: "Workshop"
        Tags: "Popular", "Premium", "Limited Seats"

ALTERNATIVES NOT USED:
    - Boolean fields (is_popular, is_new): Not scalable, hard-coded
    - Selection field: Can only pick one, not flexible
    - Free text: No consistency, no filtering, no color coding
"""

from odoo import models, fields


class ServiceEventTag(models.Model):
    """
    Tag master data for service events.

    TECHNICAL CHARACTERISTICS:
        - Simple flat structure (no hierarchy)
        - Colorized for UI display
        - Minimal fields (name + color)

    MODEL TYPE:
        Inherits from models.Model (standard persistent model)

    USAGE PATTERN:
        Many2many relationship with service.event model
        Displayed as colored badges in Kanban/Form views
    """

    _name = 'service.event.tag'
    _description = 'Service Event Tag'

    # ========================================================================
    # BASIC FIELDS
    # ========================================================================

    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True,
        help='Name of the tag (e.g., Popular, New, Premium)',
    )
    # WHY TRANSLATE:
    #   - Tags shown on website (multi-language support needed)
    #   - Example: "Popular" → "Populaire" (French)

    color = fields.Integer(
        string='Color',
        default=0,
        help='Color index for badge display (0-11)',
    )
    # COLOR FIELD:
    #   - Odoo uses integer color index (0-11)
    #   - Mapped to predefined colors in web client
    #   - Used by many2many_tags widget for colored badges
    #
    # WHY INTEGER NOT HEX:
    #   - Odoo's many2many_tags widget expects integer
    #   - Color palette is standardized across Odoo
    #   - Ensures UI consistency
    #
    # COLOR MAPPING (Odoo standard):
    #   0: White, 1: Red, 2: Orange, 3: Yellow
    #   4: Light Blue, 5: Dark Purple, 6: Salmon
    #   7: Medium Blue, 8: Dark Blue, 9: Fuchsia
    #   10: Green, 11: Purple

    # ========================================================================
    # ACTIVE FIELD
    # ========================================================================

    active = fields.Boolean(
        default=True,
        help='Uncheck to archive the tag without deleting it',
    )
    # Same pattern as category model
    # Allows archiving tags that are no longer used
    # Preserves historical data (services may reference old tags)

    # ========================================================================
    # DISPLAY NAME
    # ========================================================================

    _rec_name = 'name'
    # Simple model: display name is just the tag name
    # For more complex models, could override _compute_display_name()
    # Example: "Popular (10 services)" - but that's overkill for tags

    # ========================================================================
    # SQL CONSTRAINTS
    # ========================================================================
    # NOTE: _sql_constraints shows deprecation warning in Odoo 19
    #       but new Constraint API not yet available - safe to use

    _sql_constraints = [
        (
            'unique_tag_name',
            'UNIQUE(name)',
            'Tag name must be unique!'
        ),
    ]
    # WHY UNIQUE NAME:
    #   - Prevents duplicate tags ("Popular", "popular", "POPULAR")
    #   - Case-sensitive in PostgreSQL (could add case-insensitive if needed)
    #
    # WHY SQL CONSTRAINT:
    #   - Database-level enforcement (prevents race conditions)
    #   - Faster than Python validation
    #   - Works even with direct SQL inserts

    # ========================================================================
    # NOTE: No _auto_init() override needed
    # ========================================================================
    # WHY:
    #   - Simple model with low query volume
    #   - Name already indexed due to UNIQUE constraint
    #   - No complex queries that need optimization
    #
    # WHEN TO ADD:
    #   - If tags become frequently filtered
    #   - If tag count grows to thousands
    #   - If performance monitoring shows slow queries
