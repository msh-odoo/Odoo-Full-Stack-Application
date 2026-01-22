# Service Event Base Module

**Version:** 19.1.0.0
**Category:** Services/Events
**License:** LGPL-3

## Overview

Core business logic module for the Service Event & Booking System. This module provides foundational models, business logic, security, and data management for service event operations.

## Architecture

This is a **two-module system**:
- **service_event_base** (this module): Core business logic, models, security
- **service_event_website** (companion): Website pages, portal, snippets, controllers

### Why Separate Modules?

- ✅ Base module can be used without website (API, mobile, POS)
- ✅ Cleaner dependency management
- ✅ Easier testing and maintenance
- ✅ Follows Odoo best practices (e.g., sale vs sale_management)

## Dependencies

- `base`: Core Odoo framework
- `mail`: Activity tracking and messaging

**Does NOT depend on:**
- `website` (handled by service_event_website)
- `portal` (handled by service_event_website)

## Features (Planned)

### Core Business Logic
- Service/Event catalog management
- Booking/Registration system with workflow
- Multi-company support
- Advanced ORM operations

### Security
- User groups (Service User, Service Manager)
- Access rights (model-level permissions)
- Record rules (row-level security)

### Data Management
- Auto-numbering sequences
- Master data (categories, tags)
- SQL-level optimizations

## Installation

### Module Structure
```
service_event_base/
├── __init__.py              # Module entry point
├── __manifest__.py          # Module metadata and dependencies
├── hooks.py                 # Lifecycle hooks (pre-init, post-init)
├── models/                  # Business models
│   ├── __init__.py
│   ├── service_event_category.py
│   ├── service_event_tag.py
│   ├── service_event.py
│   └── service_booking.py
├── security/                # Access control
│   ├── security.xml
│   └── ir.model.access.csv
├── data/                    # Default data
│   ├── sequences.xml
│   └── categories.xml
├── views/                   # User interface
│   ├── service_event_views.xml
│   ├── service_booking_views.xml
│   └── menus.xml
└── demo/                    # Demo data (optional)
    └── demo_data.xml
```

### Installation Lifecycle

1. **Pre-init Hook** (`hooks.pre_init_hook`)
   - Prepares database at SQL level
   - Creates materialized views
   - Creates database extensions (pg_trgm)
   - Ensures sequences exist

2. **Module Installation**
   - Odoo creates tables from model definitions
   - Loads XML data files
   - Registers models with ORM

3. **Post-init Hook** (`hooks.post_init_hook`)
   - Creates default categories via ORM
   - Creates default tags
   - Refreshes materialized views
   - Initializes configuration

### Install Command

```bash
# Development mode with demo data
./odoo-bin -d database_name -i service_event_base --dev=all

# Production mode without demo data
./odoo-bin -d database_name -i service_event_base --without-demo=all
```

## Odoo Concepts Demonstrated

### Lifecycle Hooks
- **Pre-init Hook**: Database preparation before ORM loads
- **Post-init Hook**: Data initialization after installation
- **Init Method**: Model-level database optimizations

### ORM Concepts
- Model registration and inheritance
- Field types and attributes
- SQL constraints
- Database indexes
- Materialized views

### Data Management
- XML data files with `noupdate` flag
- `ir.model.data` for XML ID resolution
- Sequence generation for auto-numbering

### Security
- Groups and categories
- Access rights (CRUD permissions)
- Record rules (domain filtering)

## Technical Highlights

### 1. Materialized View for Performance

Pre-init hook creates a materialized view for booking statistics:
```sql
CREATE MATERIALIZED VIEW service_booking_statistics AS
SELECT 
    total_bookings,
    confirmed_bookings,
    total_revenue
FROM ...
```

**Why:** Pre-computed aggregations for dashboards (faster than real-time queries)

### 2. Database Indexes

Category model creates partial indexes in `_auto_init()`:
```python
CREATE INDEX service_event_category_code_index
ON service_event_category (code)
WHERE active = true
```

**Why:** Faster lookups on frequently queried fields

### 3. PostgreSQL Extensions

Pre-init enables `pg_trgm` extension for fuzzy search:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**Why:** Enables typo-tolerant searching (similarity matching)

### 4. Smart Sequence Configuration

Booking sequence uses year-based prefixes:
```xml
<field name="prefix">BOOK/%(year)s/</field>
```

**Result:** `BOOK/2026/0001`, `BOOK/2026/0002`

### 5. Idempotent Hooks

All hooks are safe to run multiple times:
- Use `IF NOT EXISTS` / `IF EXISTS` patterns
- Check for existing data before creating
- Graceful error handling

## Magic Fields (Auto-created by Odoo)

Every model automatically gets 5 magic fields:

1. **id**: Integer primary key (auto-increment)
2. **create_date**: Timestamp when record was created
3. **create_uid**: Many2one to res.users (who created)
4. **write_date**: Timestamp of last modification
5. **write_uid**: Many2one to res.users (who last modified)

**Why automatic:**
- Every Odoo model needs tracking
- Reduces boilerplate code
- Ensures consistency across all models

## Active Field Pattern

Models use `active` field for soft deletion:
```python
active = fields.Boolean(default=True)
```

**Behavior:**
- `active=False` → Record is archived (not deleted)
- Default search filters: `[('active', '=', True)]`
- Preserves historical data
- Can be restored anytime

## Display Name Resolution

Odoo uses `_rec_name` to determine record display:
```python
_rec_name = 'name'  # Use 'name' field for display
```

**display_name** (magic field):
- Automatically computed from `_rec_name`
- Used in Many2one widgets, breadcrumbs, logs
- Can be customized via `_compute_display_name()`

## ir.model.data Explained

When you define a record with XML ID:
```xml
<record id="category_workshop" model="service.event.category">
    <field name="name">Workshops</field>
</record>
```

Odoo creates TWO records:

1. **service_event_category** table:
   - Actual category record with data

2. **ir_model_data** table:
   - module: `service_event_base`
   - name: `category_workshop`
   - model: `service.event.category`
   - res_id: (ID from table 1)

**Purpose:**
- Enables cross-module references
- Prevents duplicate creation on reinstall
- Powers module upgrades and dependencies
- Allows `self.env.ref('module.xml_id')` lookups

## Development Status

### ✅ Commit 1: Module Foundation + Hooks (CURRENT)
- Module structure
- Pre-init hook (SQL preparation)
- Post-init hook (data initialization)
- Init method (indexes)
- Category and Tag models

### 🔜 Upcoming Commits
- Commit 2: Core models + ORM concepts
- Commit 3: Computed fields + constraints
- Commit 4: Method overrides
- Commit 5: Security implementation
- Commit 6: Backend views

## Testing

After installation, verify:

1. **Categories Created:**
   ```python
   self.env['service.event.category'].search([])
   # Should return: Workshops, Conferences, Webinars, Consulting
   ```

2. **Tags Created:**
   ```python
   self.env['service.event.tag'].search([])
   # Should return: Popular, New, Limited Seats, Premium
   ```

3. **Sequence Ready:**
   ```python
   self.env['ir.sequence'].next_by_code('service.booking')
   # Should return: 'BOOK/2026/0001'
   ```

4. **Materialized View Exists:**
   ```sql
   SELECT * FROM service_booking_statistics;
   ```

## Troubleshooting

### Module Won't Install
- Check dependencies are installed (`base`, `mail`)
- Check Python syntax errors
- Review Odoo logs for detailed errors

### Pre-init Hook Fails
- Database user may lack extension creation rights
- Try manual: `CREATE EXTENSION pg_trgm;`
- Graceful degradation: Module continues without extension

### Post-init Hook Fails
- Check model imports in `models/__init__.py`
- Verify no circular dependencies
- Ensure `SUPERUSER_ID` is available

## Contributing

This module is part of a learning project demonstrating production-grade Odoo development patterns.

## License

LGPL-3

---

**Author:** Odoo Full-Stack Development Team  
**Odoo Version:** 19.0  
**Module Version:** 1.0.0
