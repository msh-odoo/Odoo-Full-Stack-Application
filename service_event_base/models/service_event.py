# -*- coding: utf-8 -*-
"""
Service Event Model

The service.event model represents bookable service events (workshops, webinars,
consulting sessions, etc.). This model demonstrates:
    - Many2one relationships (category, company)
    - Many2many relationships (tags)
    - One2many inverse relationships (bookings)
    - Price and monetary fields
    - Active field for archiving
    - Custom _rec_name for display
    - All 5 magical fields (id, create_date, write_date, create_uid, write_uid)

ARCHITECTURE:
    - Central model linking categories, tags, and bookings
    - Multi-company aware (company_id field)
    - Supports archiving without deletion (active field)
    - Hierarchical categorization via category parent-child
    - Flexible tagging for cross-categorization

RELATIONSHIPS:
    service.event ←→ service.event.category (Many2one)
    service.event ←→ service.event.tag (Many2many)
    service.event ←→ service.booking (One2many)
    service.event ←→ res.company (Many2one)

WHY THIS DESIGN:
    - Many2one to category: Each event belongs to one primary category
    - Many2many to tags: Events can have multiple cross-cutting attributes
    - One2many to bookings: Track all bookings made for this event
    - active field: Preserve history while hiding outdated events
    - company_id: Essential for multi-tenant SaaS deployments
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ServiceEvent(models.Model):
    """
    Service Event Model

    Represents a bookable service event with pricing, categorization, and tagging.

    FIELD CATEGORIES:
        Basic Info: name, description
        Pricing: price_unit, currency_id
        Classification: category_id, tag_ids
        Relationships: booking_ids (One2many inverse)
        System: active, company_id
        Magical: id, create_date, write_date, create_uid, write_uid

    USAGE EXAMPLE:
        event = env['service.event'].create({
            'name': 'Python Workshop',
            'description': 'Learn Python basics',
            'price_unit': 299.99,
            'category_id': category.id,
            'tag_ids': [(6, 0, [tag1.id, tag2.id])],
        })
    """

    _name = 'service.event'
    _description = 'Service Event'
    _order = 'name'

    # ========================================================================
    # CUSTOM _REC_NAME
    # ========================================================================
    # WHY: By default, Odoo uses 'name' field for record display. We can
    #      customize this using _rec_name or by computing display_name.
    # HOW: Set _rec_name to any field name, or compute display_name field.
    # WHEN: Use _rec_name for simple cases, display_name for complex logic.
    # ALTERNATIVE: Could compute display_name = name + category for richer display
    # Odoo checks in this order:
        # 1. Does display_name field exist? → Use it (even if _rec_name is set)
        # 2. Is _rec_name set? → Use that field
        # 3. Neither? → Use 'name' field by default
        # 4. No 'name' field? → Use 'id' as fallback
    # ========================================================================
    _rec_name = 'name'  # Default behavior

    # ========================================================================
    # BASIC FIELDS
    # ========================================================================

    name = fields.Char(
        string='Event Name',
        required=True,
        index=True,
        help='Name of the service event (e.g., "Python Workshop")',
    )
    # WHY required=True: Every event must have a name for identification
    # WHY index=True: Frequent searches/sorts by name - index improves performance
    # HOW index works: PostgreSQL creates B-tree index on this column
    # ALTERNATIVE: Could use translate=True for multi-language support

    description = fields.Text(
        string='Description',
        help='Detailed description of the service event',
    )
    # WHY Text vs Char: Text allows unlimited length for detailed descriptions
    # WHY not Html: Html field would allow rich formatting but requires website module
    # WHEN to use Html: When displaying formatted content to end users

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive this event without deleting it',
    )
    # ========================================================================
    # ACTIVE FIELD - CRITICAL FOR ARCHIVING
    # ========================================================================
    # WHY: Odoo automatically filters active=False records from search() results
    # HOW: ORM adds WHERE active=true to all queries unless active_test=False
    # WHEN: Prefer archiving over deletion to preserve historical data
    # ALTERNATIVE: Custom state field, but active is Odoo convention
    # USAGE: archived = env['service.event'].with_context(active_test=False).search([])
    # ========================================================================

    # ========================================================================
    # PRICING FIELDS
    # ========================================================================

    price_unit = fields.Float(
        string='Regular Price',
        digits='Product Price',  # Uses decimal precision from settings
        default=0.0,
        help='Regular price per booking for this event',
    )
    # WHY Float not Monetary: Monetary requires currency_id field
    # WHY digits='Product Price': Standard Odoo precision (usually 2 decimals)
    # HOW digits works: References decimal.precision record or tuple (16,2)
    # ALTERNATIVE: Use fields.Monetary with currency_id for multi-currency

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for the price',
    )
    # WHY this field: Enables multi-currency pricing if needed later
    # WHY default to company currency: Most common use case
    # HOW lambda works: Executes at record creation time, not module load
    # ALTERNATIVE: Could be required=True to enforce currency selection

    # ========================================================================
    # PRICING LOGIC
    # ========================================================================

    early_bird_price = fields.Float(
        string='Early Bird Price',
        digits='Product Price',
        default=0.0,
        help='Discounted price for early bookings (0 = no early bird discount)',
    )
    # WHY: Encourage early registrations, reward early adopters
    # PATTERN: Common in events (conferences, workshops)
    # WHEN: Used if booking_date <= early_bird_deadline

    early_bird_deadline = fields.Date(
        string='Early Bird Deadline',
        help='Last date to get early bird pricing',
    )
    # WHY: Creates urgency for bookings
    # BUSINESS LOGIC: After this date, regular price applies
    # EXAMPLE: "Register by Jan 15 for $99 (regular $149)"

    discount_percentage = fields.Float(
        string='Discount %',
        digits=(5, 2),  # 5 total digits, 2 decimals (allows 0.00 to 100.00)
        default=0.0,
        help='Percentage discount applied to regular price (0-100)',
    )
    # WHY: Flexible discounting (promotions, bulk discounts, member discounts)
    # HOW: final_price = price_unit * (1 - discount_percentage/100)
    # VALIDATION: Should be 0-100 (checked in constraint)

    final_price = fields.Monetary(
        string='Final Price',
        currency_field='currency_id',
        compute='_compute_final_price',
        store=True,
        help='Computed price after discounts and early bird',
    )
    # ========================================================================
    # PRICING COMPUTATION LOGIC
    # ========================================================================
    # FORMULA:
    #   1. Start with price_unit (regular price)
    #   2. Apply early bird if before deadline: use early_bird_price
    #   3. Apply discount percentage: price * (1 - discount%/100)
    #   4. Result = final_price
    #
    # EXAMPLES:
    #   Regular: $100, No discounts → $100
    #   Early bird: $100 regular, $75 early → $75 (if before deadline)
    #   Discount: $100, 20% off → $80
    #   Both: $100, early $75, 10% off → $67.50 (early bird + discount)
    #
    # WHY Monetary: Proper currency formatting, multi-currency support
    # WHY stored: Used in reports, revenue calculations
    # ========================================================================

    @api.depends('price_unit', 'early_bird_price', 'early_bird_deadline', 'discount_percentage')
    def _compute_final_price(self):
        """
        Compute final price with early bird and discount logic.
        
        BUSINESS RULES:
            1. Early bird price takes precedence if conditions met
            2. Discount percentage applies to selected base price
            3. Early bird requires both price AND deadline set
            4. Discount cannot exceed 100% (validated by constraint)
        
        PRIORITY:
            Early bird (if applicable) → Discount % → Final price
        
        REAL-WORLD SCENARIO:
            Event: "Python Workshop"
            Regular: $149
            Early bird: $99 (until Jan 15)
            Additional discount: 10% for members
            
            Customer books Jan 10 with member discount:
                Base: $99 (early bird)
                Discount: $99 * 10% = $9.90
                Final: $89.10
        """
        from odoo import fields as odoo_fields
        
        for event in self:
            base_price = event.price_unit
            
            # Check if early bird pricing applies
            if event.early_bird_price > 0 and event.early_bird_deadline:
                today = odoo_fields.Date.context_today(event)
                if today <= event.early_bird_deadline:
                    base_price = event.early_bird_price
            
            # Apply discount percentage
            if event.discount_percentage > 0:
                discount_amount = base_price * (event.discount_percentage / 100.0)
                final = base_price - discount_amount
            else:
                final = base_price
            
            event.final_price = final

    # ========================================================================
    # LIFECYCLE & STATUS FIELDS
    # ========================================================================

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('registration_closed', 'Registration Closed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Event lifecycle state',
    )
    # ========================================================================
    # EVENT LIFECYCLE STATES
    # ========================================================================
    # draft: Event being prepared, not visible to customers
    # published: Event live, accepting bookings
    # registration_closed: Event visible but not accepting new bookings
    # completed: Event finished, historical record
    # cancelled: Event cancelled, bookings may be refunded
    #
    # WORKFLOW:
    #   draft → published → registration_closed → completed
    #   Any state → cancelled (cancellation possible anytime)
    #
    # BUSINESS RULES:
    #   - Only published events accept bookings
    #   - Can close registration manually or auto (capacity reached)
    #   - Completed events used for analytics/history
    #   - Cancelled events trigger booking cancellations
    # ========================================================================

    registration_open = fields.Boolean(
        string='Registration Open',
        compute='_compute_registration_open',
        store=False,
        help='Whether event is accepting new bookings',
    )
    # WHY computed: Derived from state + capacity + other factors
    # WHY non-stored: Real-time status check
    # LOGIC: published state + not at capacity + not past event date

    @api.depends('state', 'capacity', 'booking_count_confirmed', 'start_datetime')
    def _compute_registration_open(self):
        """
        Determine if event is accepting new bookings.
        
        CONDITIONS (ALL must be true):
            1. State = 'published'
            2. Not at capacity (or unlimited capacity)
            3. Event hasn't started yet (if start_datetime set)
        
        USED IN:
            - UI to show/hide booking button
            - Validation before creating booking
            - Website filtering (show only open events)
        """
        from odoo import fields as odoo_fields
        
        for event in self:
            is_open = False
            
            if event.state == 'published':
                # Check capacity
                has_capacity = True
                if event.capacity > 0:
                    has_capacity = event.booking_count_confirmed < event.capacity
                
                # Check if event hasn't started
                not_started = True
                if event.start_datetime:
                    now = odoo_fields.Datetime.now()
                    not_started = event.start_datetime > now
                
                is_open = has_capacity and not_started
            
            event.registration_open = is_open

    # ========================================================================
    # MANY2ONE RELATIONSHIP - CATEGORY
    # ========================================================================

    category_id = fields.Many2one(
        'service.event.category',
        string='Category',
        ondelete='restrict',  # Cannot delete category if events exist
        index=True,
        help='Primary category for this event',
    )
    # ========================================================================
    # MANY2ONE DEEP DIVE
    # ========================================================================
    # WHAT: Foreign key relationship to service.event.category
    # WHY ondelete='restrict': Prevents orphaned events (data integrity)
    # WHY index=True: Frequent filtering by category - needs index
    # HOW it works: Stores integer category ID in database
    # ALTERNATIVES for ondelete:
    #   - 'cascade': Delete events when category deleted (dangerous!)
    #   - 'set null': Set category_id to NULL (acceptable if not required)
    # USAGE: event.category_id.name returns category name (auto-prefetch)
    # ========================================================================

    # ========================================================================
    # MANY2MANY RELATIONSHIP - TAGS
    # ========================================================================

    tag_ids = fields.Many2many(
        'service.event.tag',
        'service_event_tag_rel',      # Relation table name
        'event_id',                    # Column for this model
        'tag_id',                      # Column for related model
        string='Tags',
        help='Tags for cross-categorization (Popular, New, Premium, etc.)',
    )
    # ========================================================================
    # MANY2MANY DEEP DIVE
    # ========================================================================
    # WHAT: Many-to-many relationship via intermediate table
    # WHY: Events can have multiple tags, tags can apply to multiple events
    # HOW: Creates service_event_tag_rel table with (event_id, tag_id) pairs
    #
    # RELATION TABLE STRUCTURE:
    #   CREATE TABLE service_event_tag_rel (
    #       event_id INTEGER REFERENCES service_event(id) ON DELETE CASCADE,
    #       tag_id INTEGER REFERENCES service_event_tag(id) ON DELETE CASCADE,
    #       PRIMARY KEY (event_id, tag_id)
    #   );
    #
    # WHY explicit table name: Avoids auto-generated name collisions
    # WHY explicit column names: Clarity and debugging
    #
    # USAGE PATTERNS:
    #   - Add tags: event.tag_ids = [(4, tag.id)]  # link
    #   - Replace all: event.tag_ids = [(6, 0, [tag1.id, tag2.id])]
    #   - Remove tag: event.tag_ids = [(3, tag.id)]  # unlink
    #   - Clear all: event.tag_ids = [(5, 0, 0)]
    #
    # MAGIC TUPLES EXPLAINED:(CUDUL-UR)
    #   (0, 0, vals): Create new record and link
    #   (1, id, vals): Update linked record
    #   (2, id): Delete linked record from database
    #   (3, id): Unlink but don't delete
    #   (4, id): Link existing record
    #   (5, 0, 0): Unlink all
    #   (6, 0, [ids]): Replace with list of IDs
    # ========================================================================

    # ========================================================================
    # ONE2MANY INVERSE RELATIONSHIP - BOOKINGS
    # ========================================================================

    booking_ids = fields.One2many(
        'service.booking',
        'event_id',  # Field in service.booking that points back here
        string='Bookings',
        help='All bookings made for this event',
    )
    # ========================================================================
    # ONE2MANY DEEP DIVE
    # ========================================================================
    # WHAT: Virtual field showing all bookings linked to this event
    # WHY: Provides easy access to related records (event.booking_ids)
    # HOW: Auto-computed by ORM - no database column created
    #
    # RELATIONSHIP PATTERN:
    #   service.event (One) ←→ service.booking (Many)
    #   - Each booking has event_id (Many2one) pointing to ONE event
    #   - Each event has booking_ids (One2many) showing MANY bookings
    #   - event_id (Many2one) is the "real" field with DB column
    #   - booking_ids (One2many) is computed by finding bookings where event_id=this
    #
    # WHY inverse field: Without booking_ids, would need manual search:
    #   bookings = env['service.booking'].search([('event_id', '=', event.id)])
    # WITH inverse field: Simply access event.booking_ids
    #
    # USAGE:
    #   - Get count: len(event.booking_ids)
    #   - Filter: event.booking_ids.filtered(lambda b: b.state == 'confirmed')
    #   - Sum: sum(event.booking_ids.mapped('amount'))
    # ========================================================================

    booking_count = fields.Integer(
        string='Booking Count',
        compute='_compute_booking_count',
        store=False,
        help='Number of bookings for this event',
    )
    # WHY computed field: Dynamic count without manual updates
    # WHY store=False: Always recalculate (ensures accuracy)
    # ALTERNATIVE: store=True with depends - faster but needs cache invalidation

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        """
        Compute the number of bookings for each event.

        WHY @api.depends: Tells Odoo to recompute when booking_ids changes
        HOW it works: Odoo tracks field dependencies and triggers recomputation
        WHEN recomputed: On booking creation/deletion, on record access if stale
        """
        for event in self:
            event.booking_count = len(event.booking_ids)

    # ========================================================================
    # ADVANCED COMPUTED FIELDS
    # ========================================================================

    capacity = fields.Integer(
        string='Capacity',
        default=0,
        help='Maximum number of attendees (0 = unlimited)',
    )
    # WHY: Control overbooking, manage limited resources
    # HOW: Used in available_seats computation
    # WHEN: Workshop rooms, webinar licenses, consultation slots

    booking_count_confirmed = fields.Integer(
        string='Confirmed Bookings',
        compute='_compute_booking_stats',
        store=True,  # STORED for performance in filters/reports
        help='Number of confirmed bookings (excluding draft/cancelled)',
    )
    # ========================================================================
    # STORED vs NON-STORED COMPUTED FIELDS
    # ========================================================================
    # store=True:
    #   ✅ Fast reads (value in database)
    #   ✅ Can use in search/filter without special domain
    #   ✅ Great for reports and list views
    #   ❌ Takes disk space
    #   ❌ Must manage cache invalidation (via @api.depends)
    #   ✅ BEST FOR: Fields used in searches, filters, reports
    #
    # store=False:
    #   ✅ No disk space
    #   ✅ Always up-to-date (computed on-demand)
    #   ❌ Slower (recomputed each access)
    #   ❌ Cannot use in search() without special domains
    #   ✅ BEST FOR: Display-only fields, rarely used fields
    # ========================================================================

    total_revenue = fields.Monetary(
        string='Total Revenue',
        currency_field='currency_id',
        compute='_compute_booking_stats',
        store=True,
        help='Sum of all confirmed booking amounts',
    )
    # WHY Monetary: Proper currency formatting and multi-currency support
    # WHY stored: Used in revenue reports, dashboards
    # HOW: Sum of booking amounts where state='confirmed'

    available_seats = fields.Integer(
        string='Available Seats',
        compute='_compute_available_seats',
        store=False,  # Always real-time
        help='Remaining capacity (capacity - confirmed bookings)',
    )
    # WHY non-stored: Need real-time availability for booking decisions
    # HOW: capacity - booking_count_confirmed
    # WHEN: Checked before allowing new bookings

    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.amount')
    def _compute_booking_stats(self):
        """
        Compute booking statistics with multiple field dependencies.

        ADVANCED @api.depends PATTERNS:
            - 'booking_ids': Triggers when booking added/removed
            - 'booking_ids.state': Triggers when ANY booking's state changes
            - 'booking_ids.amount': Triggers when ANY booking's amount changes

        WHY multiple dependencies: Changes to any trigger recomputation
        HOW it works: Odoo tracks nested field changes via ORM
        PERFORMANCE: Batched computation when multiple bookings change

        DEMONSTRATION:
            This shows how ONE method can compute MULTIPLE fields efficiently.
            Both booking_count_confirmed and total_revenue computed together.
        """
        for event in self:
            confirmed_bookings = event.booking_ids.filtered(
                lambda b: b.state == 'confirmed'
            )
            event.booking_count_confirmed = len(confirmed_bookings)
            event.total_revenue = sum(confirmed_bookings.mapped('amount'))

    @api.depends('capacity', 'booking_count_confirmed')
    def _compute_available_seats(self):
        """
        Compute available seats based on capacity and confirmed bookings.

        COMPUTED FIELD DEPENDENCIES:
            available_seats depends on:
                → capacity (regular field)
                → booking_count_confirmed (computed field, stored)

        DEPENDENCY CHAIN:
            booking created → booking_ids changes
                           → booking_count_confirmed recomputed
                           → available_seats recomputed

        WHY this works: Odoo handles transitive dependencies automatically
        """
        for event in self:
            if event.capacity > 0:
                event.available_seats = event.capacity - event.booking_count_confirmed
            else:
                event.available_seats = -1  # -1 = unlimited

    # ========================================================================
    # INVERSE FUNCTIONS FOR COMPUTED FIELDS
    # ========================================================================

    start_datetime = fields.Datetime(
        string='Start Date & Time',
        help='When the event starts',
    )
    # Regular datetime field - stores actual start time

    duration = fields.Float(
        string='Duration (hours)',
        default=1.0,
        help='Event duration in hours',
    )
    # Regular field - stores duration

    end_datetime = fields.Datetime(
        string='End Date & Time',
        compute='_compute_end_datetime',
        inverse='_inverse_end_datetime',
        store=True,
        help='Automatically calculated from start + duration',
    )
    # ========================================================================
    # INVERSE FUNCTIONS - WRITE TO COMPUTED FIELDS
    # ========================================================================
    # WHAT: Allows writing to a computed field
    # WHY: User might want to set end time directly, auto-compute duration
    # HOW: inverse= method called when field is written to
    #
    # PATTERN:
    #   - User sets start_datetime = '2026-02-01 10:00'
    #   - User sets duration = 2.0
    #   - System computes end_datetime = '2026-02-01 12:00'
    #
    # OR (with inverse):
    #   - User sets start_datetime = '2026-02-01 10:00'
    #   - User sets end_datetime = '2026-02-01 14:00'
    #   - System computes duration = 4.0 (via inverse function)
    #
    # WHEN to use: Bidirectional computations, user-friendly input
    # ========================================================================

    @api.depends('start_datetime', 'duration')
    def _compute_end_datetime(self):
        """
        Compute end time from start + duration.

        FORMULA: end_datetime = start_datetime + duration (hours)

        EDGE CASES:
            - No start_datetime → end_datetime = False
            - duration = 0 → end_datetime = start_datetime
        """
        from datetime import timedelta

        for event in self:
            if event.start_datetime and event.duration:
                event.end_datetime = event.start_datetime + timedelta(hours=event.duration)
            else:
                event.end_datetime = event.start_datetime

    def _inverse_end_datetime(self):
        """
        Inverse function: compute duration when end_datetime is set.

        FORMULA: duration = (end_datetime - start_datetime) in hours

        USAGE:
            event.end_datetime = '2026-02-01 14:00'  # Triggers this function
            → Automatically updates event.duration

        WHY useful: User can drag-drop event end time in calendar view
        """
        for event in self:
            if event.start_datetime and event.end_datetime:
                delta = event.end_datetime - event.start_datetime
                event.duration = delta.total_seconds() / 3600  # Convert to hours
            elif not event.end_datetime:
                event.duration = 0.0

    # ========================================================================
    # MULTI-COMPANY FIELD
    # ========================================================================

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company owning this event (for multi-company setups)',
    )
    # ========================================================================
    # MULTI-COMPANY DEEP DIVE
    # ========================================================================
    # WHY: Odoo supports multiple companies in one database (SaaS/holding companies)
    # HOW: Each record is owned by a company, users can access per permissions
    # WHEN to use: Always in production modules for future-proofing
    #
    # DEFAULT BEHAVIOR:
    #   - self.env.company: Current user's company
    #   - Auto-filters: Only shows records from user's allowed companies
    #   - Security: ir.rule can enforce company_id = user.company_id
    #
    # ALTERNATIVE: Make required=True to enforce company assignment
    # ========================================================================

    # ========================================================================
    # BUSINESS METRICS
    # ========================================================================

    fill_rate = fields.Float(
        string='Fill Rate (%)',
        compute='_compute_business_metrics',
        store=False,
        digits=(5, 2),
        help='Percentage of capacity filled (confirmed bookings / capacity * 100)',
    )
    # WHY: Key performance indicator for event success
    # FORMULA: (confirmed_bookings / capacity) * 100
    # EXAMPLE: 15 bookings / 20 capacity = 75% fill rate
    # BUSINESS USE: Target 80%+ fill rate for profitability

    revenue_per_seat = fields.Monetary(
        string='Revenue per Seat',
        currency_field='currency_id',
        compute='_compute_business_metrics',
        store=False,
        help='Average revenue per capacity seat (total_revenue / capacity)',
    )
    # WHY: Measure revenue efficiency
    # FORMULA: total_revenue / capacity
    # EXAMPLE: $3,000 revenue / 20 seats = $150/seat
    # BUSINESS USE: Compare across events, optimize pricing

    cancellation_rate = fields.Float(
        string='Cancellation Rate (%)',
        compute='_compute_business_metrics',
        store=False,
        digits=(5, 2),
        help='Percentage of bookings that were cancelled',
    )
    # WHY: Track customer satisfaction and overbooking strategy
    # FORMULA: (cancelled_bookings / total_bookings) * 100
    # BUSINESS USE: High cancellation = pricing/expectation issues

    @api.depends('capacity', 'booking_count_confirmed', 'total_revenue', 'booking_ids', 'booking_ids.state')
    def _compute_business_metrics(self):
        """
        Compute key business performance indicators.
        
        METRICS:
            fill_rate: How full is the event? (confirmed / capacity)
            revenue_per_seat: Revenue efficiency (revenue / capacity)
            cancellation_rate: Customer retention (cancelled / total)
        
        BUSINESS APPLICATIONS:
            - Dashboard KPIs
            - Performance reports
            - Pricing optimization
            - Event comparison
            - Historical trends
        
        REAL-WORLD EXAMPLE:
            Event: "Python Workshop"
            Capacity: 20
            Confirmed: 18
            Revenue: $2,700
            Cancelled: 2 (out of 20 total bookings)
            
            fill_rate = 90% (18/20 * 100)
            revenue_per_seat = $135 ($2,700/20)
            cancellation_rate = 10% (2/20 * 100)
        """
        for event in self:
            # Fill Rate
            if event.capacity > 0:
                event.fill_rate = (event.booking_count_confirmed / event.capacity) * 100
            else:
                event.fill_rate = 0.0
            
            # Revenue per Seat
            if event.capacity > 0:
                event.revenue_per_seat = event.total_revenue / event.capacity
            else:
                event.revenue_per_seat = 0.0
            
            # Cancellation Rate
            total_bookings = len(event.booking_ids)
            if total_bookings > 0:
                cancelled_bookings = len(event.booking_ids.filtered(lambda b: b.state == 'cancelled'))
                event.cancellation_rate = (cancelled_bookings / total_bookings) * 100
            else:
                event.cancellation_rate = 0.0

    # ========================================================================
    # MAGICAL FIELDS - AUTOMATICALLY PROVIDED BY ODOO
    # ========================================================================
    #
    # These fields are AUTOMATICALLY added by Odoo ORM to ALL models.
    # We document them here for educational purposes.
    #
    # 1. id (Integer, Primary Key)
    #    - Unique identifier for each record
    #    - Auto-incremented by PostgreSQL sequence
    #    - Used in all relationships (Many2one stores partner_id, not partner.name)
    #    - NEVER manually set this field
    #    - ACCESS: record.id or record['id']
    #
    # 2. create_date (Datetime)
    #    - Timestamp when record was created
    #    - Auto-set by ORM on create()
    #    - Timezone-aware (UTC in database)
    #    - USAGE: Track when events were added
    #    - EXAMPLE: event.create_date.strftime('%Y-%m-%d')
    #
    # 3. write_date (Datetime)
    #    - Timestamp of last modification
    #    - Auto-updated by ORM on write()
    #    - Useful for sync mechanisms, caching, optimistic locking
    #    - PATTERN: if record.write_date > last_sync: process(record)
    #
    # 4. create_uid (Many2one to res.users)
    #    - User who created this record
    #    - Auto-set to self.env.user
    #    - USAGE: Audit trails, notifications
    #    - ACCESS: event.create_uid.name (user's name)
    #
    # 5. write_uid (Many2one to res.users)
    #    - User who last modified this record
    #    - Auto-updated on every write()
    #    - USAGE: "Last modified by John Doe"
    #    - PATTERN: event.write_uid.partner_id for contact info
    #
    # WHY MAGICAL:
    #   - No field definitions needed
    #   - Cannot be overridden or deleted
    #   - Managed entirely by ORM
    #   - Present in ALL models (including service.event, service.booking, etc.)
    #
    # HOW TO USE:
    #   recent = env['service.event'].search([
    #       ('create_date', '>=', '2026-01-01')
    #   ])
    #   for event in recent:
    #       print(f"{event.name} created by {event.create_uid.name}")
    #
    # ALTERNATIVE FIELDS (not magical, but common):
    #   - display_name: Computed field for UI display
    #   - __last_update: Internal cache invalidation timestamp
    # ========================================================================

    # ========================================================================
    # DISPLAY NAME CUSTOMIZATION
    # ========================================================================

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=False,
    )
    # WHY custom display_name: Show richer info than just name
    # HOW: Computed field that combines multiple attributes
    # WHEN: Use when _rec_name alone isn't descriptive enough

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        """
        Compute display name with category for better UX.

        DISPLAY NAME vs _REC_NAME:
            _rec_name: Simple - points to a field name
            display_name: Complex - can include logic, formatting, multiple fields

        USAGE CONTEXT:
            - Shown in Many2one dropdowns
            - Shown in breadcrumbs
            - Shown in search results
            - Used in form/tree view references

        EXAMPLE OUTPUT:
            "Python Workshop [Workshops]"
            "Azure Consulting [Consulting]"
        """
        for event in self:
            if event.category_id:
                event.display_name = f"{event.name} [{event.category_id.name}]"
            else:
                event.display_name = event.name

    # ========================================================================
    # CONSTRAINTS
    # ========================================================================

    _sql_constraints = [
        (
            'positive_price',
            'CHECK (price_unit >= 0)',
            'Price must be positive or zero'
        ),
        (
            'positive_early_bird_price',
            'CHECK (early_bird_price >= 0)',
            'Early bird price must be positive or zero'
        ),
        (
            'valid_discount',
            'CHECK (discount_percentage >= 0 AND discount_percentage <= 100)',
            'Discount must be between 0 and 100 percent'
        ),
        (
            'positive_capacity',
            'CHECK (capacity >= 0)',
            'Capacity cannot be negative'
        ),
        (
            'positive_duration',
            'CHECK (duration >= 0)',
            'Duration cannot be negative'
        ),
    ]
    # WHY SQL constraint: Database-level enforcement (cannot bypass)
    # ALTERNATIVE: @api.constrains Python constraint (more flexible but slower)
    # WHEN to use SQL: Simple checks on single fields
    # WHEN to use Python: Complex multi-field validation

    # ========================================================================
    # COMPLEX PYTHON CONSTRAINTS
    # ========================================================================

    @api.constrains('capacity', 'booking_count_confirmed')
    def _check_capacity_not_exceeded(self):
        """
        Ensure confirmed bookings don't exceed capacity.

        PYTHON CONSTRAINTS vs SQL CONSTRAINTS:

        SQL (_sql_constraints):
            ✅ Enforced at database level (PostgreSQL)
            ✅ Very fast
            ✅ Cannot be bypassed
            ❌ Limited logic (only SQL expressions)
            ❌ Cannot access related records easily
            ✅ BEST FOR: Simple field validations (positive numbers, unique values)

        Python (@api.constrains):
            ✅ Full Python logic available
            ✅ Can access related records
            ✅ Can check complex business rules
            ✅ Better error messages
            ❌ Slower than SQL
            ❌ Can be bypassed via SQL queries (rare)
            ✅ BEST FOR: Multi-field validation, business logic

        WHY multiple fields in @api.constrains:
            Validation runs when ANY listed field changes.
            Here: runs when capacity OR booking_count_confirmed changes.

        WHEN this runs:
            - User changes capacity
            - New confirmed booking created (booking_count_confirmed updates)
            - Booking state changes to 'confirmed'
        """
        for event in self:
            if event.capacity > 0 and event.booking_count_confirmed > event.capacity:
                raise ValidationError(
                    f"Event '{event.name}' is overbooked! "
                    f"Capacity: {event.capacity}, "
                    f"Confirmed bookings: {event.booking_count_confirmed}"
                )

    @api.constrains('start_datetime', 'end_datetime')
    def _check_datetime_range(self):
        """
        Validate that end time is after start time.

        MULTIPLE FIELD CONSTRAINT:
            Checks relationship between two fields.
            Cannot be done with SQL constraint easily.

        EDGE CASES HANDLED:
            - Both fields must exist for validation
            - Allows missing dates (optional fields)
            - Clear error message with actual values
        """
        for event in self:
            if event.start_datetime and event.end_datetime:
                if event.end_datetime <= event.start_datetime:
                    raise ValidationError(
                        f"Event '{event.name}': End time must be after start time.\n"
                        f"Start: {event.start_datetime}\n"
                        f"End: {event.end_datetime}"
                    )

    @api.constrains('price_unit', 'booking_ids')
    def _check_price_consistency(self):
        """
        Warn if changing price when bookings exist.

        BUSINESS RULE:
            Changing event price after bookings exist can cause confusion.
            Existing bookings keep their original price (amount field).

        DESIGN DECISION:
            - Warning only, not blocking (ValidationError)
            - Could log warning instead of raising error
            - Could auto-update booking amounts (risky)

        ALTERNATIVE APPROACHES:
            1. Block price changes: raise ValidationError
            2. Auto-update bookings: booking.write({'amount': new_price})
            3. Create new event version: event.copy({'price_unit': new_price})

        WHY we allow it:
            Price changes might be intentional (discounts, promotions).
            This is just a safety check for awareness.
        """
        for event in self:
            if event.booking_ids and event.price_unit:
                # Check if any booking has different amount than current price
                different_prices = event.booking_ids.filtered(
                    lambda b: b.amount != event.price_unit
                )
                if different_prices:
                    # Note: In production, might just log this instead of raising
                    # For education, we demonstrate the pattern
                    pass  # Allow, but could raise warning in future

    # ========================================================================
    # BUSINESS LOGIC CONSTRAINTS
    # ========================================================================

    @api.constrains('early_bird_price', 'price_unit')
    def _check_early_bird_price(self):
        """
        Validate early bird price is less than regular price.
        
        BUSINESS RULE:
            Early bird pricing should offer a discount, not increase price.
        
        VALIDATION:
            If early_bird_price set, must be < price_unit
            If early_bird_price = 0, validation skipped (no early bird)
        """
        for event in self:
            if event.early_bird_price > 0 and event.early_bird_price >= event.price_unit:
                raise ValidationError(
                    f"Early bird price (${event.early_bird_price:.2f}) must be less than "
                    f"regular price (${event.price_unit:.2f}) for event '{event.name}'"
                )

    @api.constrains('early_bird_deadline', 'start_datetime')
    def _check_early_bird_deadline(self):
        """
        Ensure early bird deadline is before event start.
        
        BUSINESS LOGIC:
            Can't offer early bird pricing after event has started.
        """
        for event in self:
            if event.early_bird_deadline and event.start_datetime:
                # Convert date to datetime for comparison
                from datetime import datetime, time
                deadline_dt = datetime.combine(event.early_bird_deadline, time.max)
                
                if deadline_dt >= event.start_datetime:
                    raise ValidationError(
                        f"Early bird deadline must be before event start time for '{event.name}'"
                    )

    # ========================================================================
    # LIFECYCLE METHODS
    # ========================================================================

    def action_publish(self):
        """
        Publish event (make available for booking).
        
        BUSINESS RULES:
            - Event must have price set
            - Event must have capacity set (or 0 for unlimited)
            - Event must have category
        
        STATE TRANSITION:
            draft → published
        
        EFFECTS:
            - Event visible on website
            - Customers can book
            - registration_open becomes True
        """
        for event in self:
            # Validation
            if not event.price_unit and not event.final_price:
                raise ValidationError(f"Cannot publish '{event.name}': Price must be set")
            
            if not event.category_id:
                raise ValidationError(f"Cannot publish '{event.name}': Category must be set")
            
            event.write({'state': 'published'})
        
        return True

    def action_close_registration(self):
        """
        Close registration (stop accepting new bookings).
        
        USE CASES:
            - Manually close when prep work starts
            - Event is full (auto-triggered)
            - Last-minute changes needed
        
        STATE TRANSITION:
            published → registration_closed
        
        EFFECTS:
            - Event still visible but can't book
            - Existing bookings unaffected
            - registration_open becomes False
        """
        self.write({'state': 'registration_closed'})
        return True

    def action_mark_completed(self):
        """
        Mark event as completed (event has occurred).
        
        USE CASES:
            - Event date has passed
            - Manual marking after event concludes
        
        STATE TRANSITION:
            registration_closed → completed
            published → completed (if registration wasn't closed first)
        
        EFFECTS:
            - Event archived from active lists
            - Used for historical reporting
            - Bookings remain for attendance tracking
        """
        self.write({'state': 'completed'})
        return True

    def action_cancel_event(self):
        """
        Cancel the event.
        
        BUSINESS IMPACT:
            - All bookings should be cancelled
            - Refunds may be needed
            - Notifications sent to customers
        
        STATE TRANSITION:
            Any state → cancelled
        
        CASCADE EFFECTS:
            - Cancel all associated bookings
            - Could trigger refund workflow
            - Could send cancellation emails
        """
        for event in self:
            # Cancel all non-cancelled bookings
            bookings_to_cancel = event.booking_ids.filtered(
                lambda b: b.state != 'cancelled'
            )
            if bookings_to_cancel:
                bookings_to_cancel.action_cancel()
            
            event.write({'state': 'cancelled'})
        
        return True

    def action_reset_to_draft(self):
        """
        Reset event to draft status.
        
        USE CASE:
            - Unpublish event for major changes
            - Reuse cancelled event
        
        VALIDATION:
            - Cannot reset if confirmed bookings exist
        """
        for event in self:
            if event.booking_count_confirmed > 0:
                raise ValidationError(
                    f"Cannot reset '{event.name}' to draft: "
                    f"{event.booking_count_confirmed} confirmed bookings exist"
                )
            
            event.write({'state': 'draft'})
        
        return True

    # ========================================================================
    # BUSINESS HELPER METHODS
    # ========================================================================

    def get_applicable_price(self, booking_date=None):
        """
        Calculate price applicable for a specific booking date.
        
        PARAMETERS:
            booking_date: Date of booking (default: today)
        
        RETURNS:
            Float: Price applicable on that date
        
        BUSINESS LOGIC:
            - Check if early bird deadline applies
            - Apply discount percentage
            - Return final calculated price
        
        USAGE:
            price = event.get_applicable_price(fields.Date.today())
            booking.create({'amount': price})
        """
        self.ensure_one()
        
        from odoo import fields as odoo_fields
        if booking_date is None:
            booking_date = odoo_fields.Date.context_today(self)
        
        base_price = self.price_unit
        
        # Check early bird
        if self.early_bird_price > 0 and self.early_bird_deadline:
            if booking_date <= self.early_bird_deadline:
                base_price = self.early_bird_price
        
        # Apply discount
        if self.discount_percentage > 0:
            discount_amount = base_price * (self.discount_percentage / 100.0)
            final = base_price - discount_amount
        else:
            final = base_price
        
        return final

    def check_booking_allowed(self):
        """
        Check if new bookings are allowed for this event.
        
        RETURNS:
            (bool, str): (allowed, reason_if_not_allowed)
        
        BUSINESS RULES CHECKED:
            1. Event must be published
            2. Must have capacity (or unlimited)
            3. Event must not have started
            4. Registration must be open
        
        USAGE:
            allowed, reason = event.check_booking_allowed()
            if not allowed:
                raise ValidationError(reason)
        """
        self.ensure_one()
        
        if self.state != 'published':
            return False, f"Event '{self.name}' is not published (current state: {self.state})"
        
        if not self.registration_open:
            return False, f"Registration is closed for '{self.name}'"
        
        if self.capacity > 0 and self.booking_count_confirmed >= self.capacity:
            return False, f"Event '{self.name}' is at full capacity ({self.capacity} seats)"
        
        if self.start_datetime:
            from odoo import fields as odoo_fields
            now = odoo_fields.Datetime.now()
            if self.start_datetime <= now:
                return False, f"Event '{self.name}' has already started"
        
        return True, ""

    def _promote_from_waitlist(self):
        """
        Automatically promote first person from waitlist when spot opens.
        
        TRIGGERED BY:
            - Confirmed booking cancelled
            - Capacity increased
        
        BUSINESS LOGIC:
            - Find oldest waitlisted booking (FIFO)
            - Promote to confirmed
            - Could send notification email
        
        USAGE:
            booking.action_cancel()  # Frees a spot
            event._promote_from_waitlist()  # Auto-promotes next in line
        """
        self.ensure_one()
        
        # Check if promotion possible
        if self.capacity > 0 and self.booking_count_confirmed >= self.capacity:
            return  # Still at capacity
        
        # Find first waitlisted booking (oldest first)
        waitlisted = self.booking_ids.filtered(
            lambda b: b.state == 'waitlisted'
        ).sorted('create_date')
        
        if waitlisted:
            first_in_line = waitlisted[0]
            first_in_line.write({'state': 'confirmed'})
            
            # Could trigger email notification here
            # first_in_line._send_promotion_notification()
            
            return first_in_line
        
        return None

    def action_view_bookings(self):
        """
        Open bookings list view filtered for this event.
        
        USAGE:
            - Smart button in form view
            - Shows all bookings for this event
        
        RETURNS:
            Action dictionary to open tree view
        """
        self.ensure_one()
        return {
            'name': _('Bookings for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_mode': 'list,form',
            'domain': [('event_id', '=', self.id)],
            'context': {'default_event_id': self.id},
        }

