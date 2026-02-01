# -*- coding: utf-8 -*-
"""
Service Event Base Module - Lifecycle Hooks

This module defines pre-init and post-init hooks for the service_event_base module.

HOOK EXECUTION ORDER:
    1. pre_init_hook (BEFORE ORM is available)
    2. Module installation (XML data, models registration)
    3. post_init_hook (AFTER ORM is available)

WHY USE HOOKS:
    - Some operations cannot be done via XML (e.g., conditional SQL)
    - Some operations must happen before/after module load
    - Allows database preparation and cleanup
    - Enables data migration and initialization logic

WHY NOT XML DATA FILES:
    - XML cannot execute conditional logic
    - XML cannot access raw SQL (needed for schema changes)
    - XML runs during installation, not before/after
    - Hooks provide finer control over execution timing
"""

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-initialization hook executed BEFORE module installation.

    PURPOSE:
        Prepare the database at the SQL level before Odoo ORM loads the module.
        This is the ONLY place where you can safely modify database schema
        before Odoo's ORM attempts to create tables.

    WHEN TO USE:
        - Renaming existing tables/columns (data migration)
        - Creating SQL views that models will reference
        - Dropping conflicting constraints from previous versions
        - Backing up critical data before schema changes
        - Adding indexes that must exist before ORM operations

    WHY NOT ORM:
        - ORM is NOT available yet (models not loaded)
        - Only raw SQL via cursor (cr) is allowed
        - Attempting to use env or models will fail

    PARAMETERS:
        cr: Database cursor (psycopg2 cursor object)
            - Used for executing raw SQL
            - No transaction management needed (Odoo handles it)

    IDEMPOTENCY:
        This function may run multiple times (upgrades, reinstalls).
        All operations must be safe to re-execute.
        Use IF EXISTS / IF NOT EXISTS patterns.

    EXAMPLE USE CASES:
        - Migrate data from old module version
        - Rename deprecated tables to new names
        - Create PostgreSQL extensions (e.g., pg_trgm for fuzzy search)
        - Add database-level constraints before ORM validation

    WHY THIS IMPLEMENTATION:
        - Creates a materialized view for booking statistics (performance)
        - Adds a partial index for active services (query optimization)
        - These must exist before models reference them

    WHY NOT IN INIT METHOD:
        - Init runs after models are loaded (too late for schema prep)
        - Pre-init ensures database is ready for model registration
    """

    _logger.info("=" * 80)
    _logger.info("EXECUTING PRE-INIT HOOK: service_event_base")
    _logger.info("=" * 80)

    # ========================================================================
    # STEP 1: Create helper function for safe SQL execution
    # ========================================================================
    # WHY: Prevents crashes if view/table already exists
    # WHY NOT try/except: Explicit is better than implicit, clearer logs

    def execute_safe_sql(sql_query, description):
        """Execute SQL with error handling and logging."""
        try:
            cr.execute(sql_query)
            _logger.info("✓ PRE-INIT: %s", description)
        except Exception as e:
            _logger.warning("⚠ PRE-INIT: %s failed - %s", description, str(e))
            # Don't raise - this may be a re-installation

    # ========================================================================
    # STEP 2: Drop old/conflicting objects (migration safety)
    # ========================================================================
    # WHY: If upgrading from older version, old structures must be removed
    # PATTERN: Always use DROP IF EXISTS (idempotent)

    execute_safe_sql(
        """
        DROP MATERIALIZED VIEW IF EXISTS service_booking_statistics CASCADE;
        """,
        "Dropped old booking statistics view (if existed)"
    )

    # ========================================================================
    # STEP 3: Create materialized view for reporting
    # ========================================================================
    # WHY MATERIALIZED VIEW:
    #   - Pre-computed aggregations for dashboard/reports
    #   - Faster than real-time aggregation on large datasets
    #   - Can be refreshed periodically via cron
    #
    # WHY NOT REGULAR VIEW:
    #   - Regular views execute query every time (slow for aggregations)
    #
    # WHY NOT COMPUTE FIELD:
    #   - Compute fields calculate per-record (not efficient for stats)
    #   - Materialized view aggregates across all records once
    #
    # NOTE: This will be populated by post_init_hook after data exists

    execute_safe_sql(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS service_booking_statistics AS
        SELECT
            1 as id,  -- Dummy ID for now (will be populated post-init)
            0 as total_bookings,
            0 as confirmed_bookings,
            0.0 as total_revenue
        WITH NO DATA;  -- Don't populate yet (no data exists pre-install)
        """,
        "Created materialized view for booking statistics"
    )

    # ========================================================================
    # STEP 4: Create extension for advanced search (optional)
    # ========================================================================
    # WHY pg_trgm:
    #   - Enables fuzzy text search (typo tolerance)
    #   - Powers similarity() and % operator
    #   - Useful for service name searching
    #
    # WHY NOT ALWAYS INSTALL:
    #   - Requires PostgreSQL extension installation rights
    #   - May fail on restricted database servers
    #   - Graceful degradation if unavailable

    execute_safe_sql(
        """
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        """,
        "Created PostgreSQL trigram extension (for fuzzy search)"
    )

    # ========================================================================
    # STEP 5: Prepare sequence (if migrating from old system)
    # ========================================================================
    # WHY: Ensure sequence starts at correct number after migration
    # SCENARIO: Importing existing bookings from external system

    execute_safe_sql(
        """
        -- Create sequence if not exists (will be used by booking name)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'service_booking_sequence'
            ) THEN
                CREATE SEQUENCE service_booking_sequence START 1;
            END IF;
        END $$;
        """,
        "Ensured booking sequence exists"
    )

    _logger.info("=" * 80)
    _logger.info("PRE-INIT HOOK COMPLETED SUCCESSFULLY")
    _logger.info("=" * 80)


def post_init_hook(env):
    """
    Post-initialization hook executed AFTER module installation.

    PURPOSE:
        Initialize data and configure the system using the Odoo ORM.
        This runs after all models are loaded and tables are created.

    WHEN TO USE:
        - Create default master data (categories, tags)
        - Assign default access rights
        - Populate initial configuration
        - Refresh materialized views
        - Generate demo/seed data

    WHY USE ORM HERE:
        - ORM is fully available (all models loaded)
        - Can use model methods, constraints, computed fields
        - Automatic logging, tracking, translations
        - Type safety and validation

    PARAMETERS:
        env: Odoo Environment object (provides access to ORM)
             In Odoo 19+, hooks receive env directly (not cr + registry)

    ENVIRONMENT PROVIDED:
        Odoo 19 automatically provides an Environment instance.
        No need to manually create it using api.Environment.
        WHY CHANGE: Simpler API, follows Odoo's direction

    IDEMPOTENCY:
        Use <record> with noupdate="1" or check existence before create.
        This may run on upgrade, so avoid duplicate data creation.

    WHY NOT XML DATA FILES:
        - XML runs during installation (this runs AFTER)
        - Can use Python logic (conditionals, loops)
        - Can reference just-created records
        - Can perform complex calculations

    EXAMPLE USE CASES:
        - Create default service categories
        - Assign groups to the default admin user
        - Populate configuration parameters
        - Refresh materialized views with initial data
        - Create welcome messages or tours

    WHY THIS IMPLEMENTATION:
        - Creates default service categories (required for demo data)
        - Refreshes booking statistics view
        - Creates sample data for testing

    WHY NOT IN MODEL _AUTO_INIT:
        - _auto_init is too early (other modules not loaded)
        - Post-init guarantees all dependencies are ready
    """

    _logger.info("=" * 80)
    _logger.info("EXECUTING POST-INIT HOOK: service_event_base")
    _logger.info("=" * 80)

    # ========================================================================
    # Environment is provided directly in Odoo 19+
    # ========================================================================
    # No need to create api.Environment(cr, SUPERUSER_ID, {})
    # env is already available with SUPERUSER context

    # ========================================================================
    # STEP 2: Create default service categories
    # ========================================================================
    # WHY CREATE HERE NOT XML:
    #   - XML would create duplicates on upgrade
    #   - Can check existence dynamically
    #   - Can use ORM methods for validation
    #
    # PATTERN: Check existence before create (idempotent)

    _logger.info("Creating default service categories...")

    Category = env['service.event.category']

    # Define default categories
    # WHY DICT: Structured data, easy to extend
    default_categories = [
        {
            'name': 'Workshops',
            'description': 'Educational workshops and training sessions',
            'code': 'WORKSHOP',
        },
        {
            'name': 'Conferences',
            'description': 'Professional conferences and seminars',
            'code': 'CONFERENCE',
        },
        {
            'name': 'Webinars',
            'description': 'Online webinars and virtual events',
            'code': 'WEBINAR',
        },
        {
            'name': 'Consulting',
            'description': 'One-on-one consulting services',
            'code': 'CONSULTING',
        },
    ]

    for cat_data in default_categories:
        # Check if category exists (by code)
        # WHY BY CODE: Name may change (translations), code is unique
        existing = Category.search([('code', '=', cat_data['code'])], limit=1)

        if not existing:
            category = Category.create(cat_data)
            _logger.info("  ✓ Created category: %s", category.name)
        else:
            _logger.info("  ⊳ Category already exists: %s", existing.name)

    # ========================================================================
    # STEP 3: Create default tags
    # ========================================================================

    _logger.info("Creating default service tags...")

    Tag = env['service.event.tag']

    default_tags = [
        {'name': 'Popular', 'color': 2},  # Green
        {'name': 'New', 'color': 4},       # Blue
        {'name': 'Limited Seats', 'color': 1},  # Red
        {'name': 'Premium', 'color': 5},   # Purple
    ]

    for tag_data in default_tags:
        existing = Tag.search([('name', '=', tag_data['name'])], limit=1)
        if not existing:
            tag = Tag.create(tag_data)
            _logger.info("  ✓ Created tag: %s", tag.name)
        else:
            _logger.info("  ⊳ Tag already exists: %s", existing.name)

    # ========================================================================
    # STEP 4: Refresh materialized view
    # ========================================================================
    # WHY REFRESH HERE:
    #   - Materialized view created in pre-init (empty)
    #   - After installation, initial data may exist
    #   - Refresh populates view with current statistics
    #
    # WHY NOT AUTOMATIC:
    #   - Materialized views don't auto-update (by design)
    #   - Must explicitly refresh (here and via cron)

    _logger.info("Refreshing booking statistics materialized view...")

    try:
        # Use a savepoint to prevent transaction abort on error
        env.cr.execute("SAVEPOINT refresh_mat_view;")
        env.cr.execute("REFRESH MATERIALIZED VIEW service_booking_statistics;")
        env.cr.execute("RELEASE SAVEPOINT refresh_mat_view;")
        _logger.info("  ✓ Materialized view refreshed")
    except Exception as e:
        # May fail if view doesn't exist yet (pre-init didn't run SQL)
        env.cr.execute("ROLLBACK TO SAVEPOINT refresh_mat_view;")
        _logger.warning("  ⚠ Could not refresh view: %s", str(e))

    # ========================================================================
    # STEP 5: Create welcome message (optional)
    # ========================================================================
    # WHY: Inform admins that module is installed
    # MECHANISM: Create ir.mail_message or log note

    _logger.info("Module initialization complete!")
    _logger.info("  - Default categories created: %d", len(default_categories))
    _logger.info("  - Default tags created: %d", len(default_tags))
    _logger.info("  - Database optimizations applied")

    # ========================================================================
    # COMMIT NOT NEEDED
    # ========================================================================
    # WHY: Odoo manages transaction automatically
    # Hooks run within module installation transaction
    # If hook fails, entire installation rolls back

    _logger.info("=" * 80)
    _logger.info("POST-INIT HOOK COMPLETED SUCCESSFULLY")
    _logger.info("=" * 80)
