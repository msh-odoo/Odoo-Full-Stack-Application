# -*- coding: utf-8 -*-
"""
Service Booking Model

The service.booking model represents customer bookings for service events.
This model demonstrates:
    - Sequence-based auto-numbering (booking_number)
    - Selection fields with state workflow
    - Many2one relationships (partner, event, company)
    - Computed fields with dependencies
    - Default values and auto-computation
    - All 5 magical fields
    - Custom _rec_name using sequence field

ARCHITECTURE:
    - Transactional model (creates booking records)
    - Links customers (partners) to events
    - State-based workflow (draft → confirmed → done → cancelled)
    - Amount auto-computed from event price
    - Unique booking numbers via ir.sequence

RELATIONSHIPS:
    service.booking ←→ res.partner (Many2one)
    service.booking ←→ service.event (Many2one)
    service.booking ←→ res.company (Many2one)
    service.booking ←→ res.users (Many2one, magical: create_uid, write_uid)

STATE WORKFLOW:
    draft → confirmed → done
              ↓
          cancelled (terminal state)

WHY THIS DESIGN:
    - State field: Track booking lifecycle
    - booking_number: Human-readable unique identifier
    - partner_id: Essential for CRM integration
    - event_id: Links to service being booked
    - amount: Snapshot of price at booking time (not live-computed)
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ServiceBooking(models.Model):
    """
    Service Booking Model

    Represents a customer's booking for a service event.

    FIELD CATEGORIES:
        Identification: booking_number (sequence-based), name (computed)
        Relationships: partner_id, event_id
        Workflow: state, booking_date
        Financial: amount, currency_id
        System: company_id, active
        Magical: id, create_date, write_date, create_uid, write_uid

    USAGE EXAMPLE:
        booking = env['service.booking'].create({
            'partner_id': partner.id,
            'event_id': event.id,
            'booking_date': fields.Date.today(),
        })
        booking.action_confirm()
    """

    _name = 'service.booking'
    _description = 'Service Booking'
    _order = 'booking_date desc, id desc'

    # ========================================================================
    # CUSTOM _REC_NAME - USING SEQUENCE FIELD
    # ========================================================================
    # WHY: booking_number is more meaningful than partner name for bookings
    # HOW: Set _rec_name to point to sequence field
    # WHEN: Use when you have a unique human-readable identifier
    # ALTERNATIVE: Use display_name computed field for complex patterns
    # RESULT: Booking displayed as "BOOK/2026/0001" not "John Doe"
    # ========================================================================
    _rec_name = 'booking_number'

    # ========================================================================
    # SEQUENCE-BASED AUTO-NUMBERING
    # ========================================================================

    booking_number = fields.Char(
        string='Booking Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique booking number (e.g., BOOK/2026/0001)',
    )
    # ========================================================================
    # SEQUENCE FIELD DEEP DIVE
    # ========================================================================
    # WHAT: Auto-generated unique identifier using ir.sequence
    # WHY: Provides human-readable, sequential numbering
    # HOW: Generated in create() method via env['ir.sequence'].next_by_code()
    #
    # FIELD ATTRIBUTES:
    #   - required=True: Must have a value (set in create)
    #   - copy=False: Duplicated records get new numbers
    #   - readonly=True: Users cannot manually edit
    #   - default='New': Placeholder until actual number generated
    #
    # GENERATION PATTERN:
    #   1. User creates booking (booking_number = 'New')
    #   2. create() method intercepts
    #   3. Calls ir.sequence.next_by_code('service.booking')
    #   4. Replaces 'New' with 'BOOK/2026/0001'
    #
    # SEQUENCE CONFIGURATION:
    #   Defined in data/sequences.xml:
    #   - Code: service.booking
    #   - Prefix: BOOK/%(year)s/
    #   - Padding: 4 digits (0001, 0002, ...)
    #   - Implementation: PostgreSQL sequence for concurrency safety
    #
    # WHY copy=False:
    #   When duplicating a booking (record.copy()), Odoo would copy all fields.
    #   copy=False ensures duplicated bookings get NEW numbers, not clones.
    #
    # ALTERNATIVE PATTERNS:
    #   - Use UUID: random but not sequential
    #   - Use create_date: not unique
    #   - Manual numbering: user errors, gaps, concurrency issues
    # ========================================================================

    name = fields.Char(
        string='Booking Name',
        compute='_compute_name',
        store=True,
        help='Computed name combining booking number and event',
    )
    # WHY computed name: Combines booking_number + event for richer display
    # WHY store=True: Cached in database for fast searches/sorts
    # ALTERNATIVE: Use display_name instead of separate name field

    @api.depends('booking_number', 'event_id.name')
    def _compute_name(self):
        """
        Compute booking name from number and event.

        WHY store=True here: Frequently displayed/searched
        PATTERN: "BOOK/2026/0001 - Python Workshop"
        """
        for booking in self:
            if booking.event_id:
                booking.name = f"{booking.booking_number} - {booking.event_id.name}"
            else:
                booking.name = booking.booking_number

    # ========================================================================
    # MANY2ONE RELATIONSHIPS
    # ========================================================================

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='restrict',
        index=True,
        help='Customer making this booking',
    )
    # ========================================================================
    # PARTNER (CUSTOMER) RELATIONSHIP
    # ========================================================================
    # WHAT: Links booking to a customer (res.partner)
    # WHY required=True: Every booking must have a customer
    # WHY ondelete='restrict': Cannot delete customer with active bookings
    #
    # res.partner EXPLAINED:
    #   - Central contact model in Odoo
    #   - Represents customers, vendors, companies, individuals
    #   - Provides: name, email, phone, address, etc.
    #   - Used across all Odoo modules (sales, purchases, CRM, etc.)
    #
    # USAGE:
    #   booking.partner_id.name → Customer name
    #   booking.partner_id.email → Customer email
    #   booking.partner_id.commercial_partner_id → Parent company
    # ========================================================================

    event_id = fields.Many2one(
        'service.event',
        string='Event',
        required=True,
        ondelete='restrict',
        index=True,
        help='Service event being booked',
    )
    # WHY required=True: Booking without event makes no sense
    # WHY index=True: Frequent filtering "show all bookings for event X"
    # INVERSE: event.booking_ids shows all bookings for that event

    # ========================================================================
    # STATE FIELD - WORKFLOW MANAGEMENT
    # ========================================================================

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waitlisted', 'Waitlisted'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Booking workflow state',
    )
    # ========================================================================
    # SELECTION FIELD DEEP DIVE
    # ========================================================================
    # WHAT: Field with predefined list of values
    # WHY: Enforces valid states, enables workflow logic
    # HOW: Stored as VARCHAR in database, constrained by selection list
    #
    # SELECTION FORMAT:
    #   List of tuples: [(database_value, 'Display Label'), ...]
    #   - First element: Stored in database (use lowercase, underscores)
    #   - Second element: Shown to user (translatable)
    #
    # tracking=True EXPLAINED:
    #   - Enables change tracking in chatter
    #   - Logs: "Status changed from Draft to Confirmed by John Doe"
    #   - Requires mail module (included in base)
    #   - Creates mail.tracking.value records
    #
    # STATE WORKFLOW LOGIC:
    #   Draft → Waitlisted (if event full)
    #   Draft → Confirmed (if space available): action_confirm()
    #   Waitlisted → Confirmed (when spot opens): action_confirm()
    #   Confirmed → Done: action_done()
    #   * → Cancelled: action_cancel()
    #
    # Added 'waitlisted' state for capacity management
    #
    # BEST PRACTICES:
    #   - Use lowercase_underscore for database values
    #   - Use Title Case for labels
    #   - Add tracking=True for workflow fields
    #   - Implement action_* methods for transitions
    #
    # ALTERNATIVE:
    #   - Could use Many2one to separate state table (overkill for simple workflows)
    #   - Could use Integer with constants (less readable)
    # ========================================================================

    # ========================================================================
    # WAITLIST MANAGEMENT
    # ========================================================================

    is_waitlisted = fields.Boolean(
        string='On Waitlist',
        compute='_compute_is_waitlisted',
        store=True,
        help='Automatically set when event is at capacity',
    )
    # WHY: Quick filter for waitlisted bookings
    # HOW: Derived from state = 'waitlisted'
    # STORED: For fast searches "show all waitlisted bookings"

    waitlist_position = fields.Integer(
        string='Waitlist Position',
        compute='_compute_waitlist_position',
        store=False,
        help='Position in waitlist queue (1 = next in line)',
    )
    # WHY: Show customers their position in waitlist
    # HOW: Order waitlisted bookings by create_date
    # NON-STORED: Real-time position (changes as others cancel)

    @api.depends('state')
    def _compute_is_waitlisted(self):
        """Flag bookings that are waitlisted."""
        for booking in self:
            booking.is_waitlisted = (booking.state == 'waitlisted')

    @api.depends('event_id', 'event_id.booking_ids', 'event_id.booking_ids.state', 'event_id.booking_ids.create_date')
    def _compute_waitlist_position(self):
        """
        Calculate position in waitlist queue.

        LOGIC:
            - Only for waitlisted bookings
            - Ordered by creation date (first-come-first-served)
            - Position 1 = next to be promoted

        BUSINESS USE:
            - Show customer: "You are #3 in line"
            - Auto-promote: promote position 1 when spot opens
        """
        for booking in self:
            if booking.state == 'waitlisted' and booking.event_id:
                # Get all waitlisted bookings for this event, ordered by creation date
                waitlisted = booking.event_id.booking_ids.filtered(
                    lambda b: b.state == 'waitlisted'
                ).sorted('create_date')

                # Find position in queue (1-indexed)
                try:
                    booking.waitlist_position = list(waitlisted.ids).index(booking.id) + 1
                except ValueError:
                    booking.waitlist_position = 0
            else:
                booking.waitlist_position = 0

    # ========================================================================
    # DATE/TIME FIELDS
    # ========================================================================

    booking_date = fields.Date(
        string='Booking Date',
        default=fields.Date.context_today,
        required=True,
        help='Date when this booking was made',
    )
    # ========================================================================
    # DATE vs DATETIME vs DATE.TODAY vs CONTEXT_TODAY
    # ========================================================================
    # DATE FIELD:
    #   - Stores date only (no time): '2026-01-22'
    #   - Database: DATE type
    #   - Use for: birthdays, deadlines, event dates
    #
    # DATETIME FIELD:
    #   - Stores date + time: '2026-01-22 14:30:00'
    #   - Database: TIMESTAMP (always UTC)
    #   - Use for: transactions, logs, appointments
    #
    # DEFAULT OPTIONS:
    #   - fields.Date.today(): Server's current date (UTC)
    #   - fields.Date.context_today(self): User's timezone-aware date
    #   - lambda self: fields.Date.today(): Same as Date.today()
    #
    # WHY context_today:
    #   - Respects user timezone
    #   - User in NY (UTC-5) sees today = Jan 22
    #   - Server in UTC sees today = Jan 23 at 2am
    #   - context_today ensures consistent UX
    #
    # DEFAULT VALUE FUNCTIONS
    # DEFAULT PATTERNS DEMONSTRATED:
    #   1. Static default: default='draft'
    #   2. Function reference: default=fields.Date.context_today
    #   3. Lambda: default=lambda self: self.env.company
    #   4. Method: default=_default_company_id
    #
    # WHEN each executes:
    #   - Function/lambda: Called EVERY TIME a new record is created
    #   - Static: Set ONCE at field definition
    #
    # MAGICAL FIELDS USAGE:
    #   - create_date: Exact timestamp (UTC) when record created
    #   - booking_date: Business date chosen by user (timezone-aware)
    # ========================================================================

    # ========================================================================
    # FINANCIAL FIELDS
    # ========================================================================

    amount = fields.Float(
        string='Amount',
        digits='Product Price',
        compute='_compute_amount',
        store=True,
        readonly=False,  # Allow manual override
        help='Booking amount (auto-computed from event price)',
    )
    # WHY computed: Auto-fills from event price
    # WHY store=True: Preserves amount even if event price changes later
    # WHY readonly=False: Allows discounts/overrides
    # PATTERN: Copy-on-write (snapshot of event price at booking time)

    @api.depends('event_id', 'event_id.price_unit')
    def _compute_amount(self):
        """
        Compute amount from event price.

        WHY SNAPSHOT PATTERN:
            - Booking amount should not change if event price changes later
            - store=True ensures amount is saved to database
            - Once saved, it becomes independent of event price

        WHEN COMPUTED:
            - On event_id change (selecting event)
            - On event.price_unit change (event price updated)
            - NOT recomputed after booking is confirmed (snapshot preserved)
        """
        for booking in self:
            if booking.event_id:
                booking.amount = booking.event_id.price_unit
            else:
                booking.amount = 0.0

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='event_id.currency_id',
        store=True,
        help='Currency from the event',
    )
    # ========================================================================
    # RELATED FIELDS
    # ========================================================================
    # WHAT: Shortcut to access related record's field
    # WHY: Avoids repetitive booking.event_id.currency_id
    # HOW: related='event_id.currency_id' creates automatic delegation
    #
    # WITH related field: booking.currency_id
    # WITHOUT related field: booking.event_id.currency_id
    #
    # store=True: Copy currency to booking table
    #   - Pros: Faster queries, preserved if event deleted
    #   - Cons: Duplicated data, sync issues if event currency changes
    #
    # store=False (default): Computed on-the-fly
    #   - Pros: Always in sync, no data duplication
    #   - Cons: Requires JOIN in queries, fails if event deleted
    #
    # WHEN to store:
    #   - Snapshot pattern (preserve value)
    #   - Frequently queried/filtered
    #   - Related record might be deleted
    # ========================================================================

    # ========================================================================
    # SYSTEM FIELDS
    # ========================================================================

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive this booking',
    )
    # Same pattern as service.event.active (archive instead of delete)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company owning this booking',
    )
    # Multi-company support (same pattern as service.event)

    # ========================================================================
    # MAGICAL FIELDS - AUTOMATIC AUDIT TRAIL
    # ========================================================================
    #
    # All 5 magical fields are automatically available:
    #
    # 1. id - Unique record identifier
    #    USAGE: booking.id → 42
    #
    # 2. create_date - Record creation timestamp
    #    USAGE: booking.create_date → datetime.datetime(2026, 1, 22, 14, 30)
    #    PATTERN: Recent bookings = search([('create_date', '>=', date)])
    #
    # 3. write_date - Last modification timestamp
    #    USAGE: booking.write_date → datetime.datetime(2026, 1, 22, 15, 45)
    #    PATTERN: Changed since = search([('write_date', '>', last_check)])
    #
    # 4. create_uid - User who created the record
    #    USAGE: booking.create_uid.name → "John Doe"
    #    PATTERN: My bookings = search([('create_uid', '=', env.uid)])
    #
    # 5. write_uid - User who last modified the record
    #    USAGE: booking.write_uid.partner_id.email → "admin@example.com"
    #    PATTERN: audit_log = f"Last edited by {booking.write_uid.name}"
    #
    # COMBINING MAGICAL FIELDS:
    #   # Get bookings created today by current user
    #   today_mine = env['service.booking'].search([
    #       ('create_date', '>=', fields.Datetime.now().replace(hour=0, minute=0)),
    #       ('create_uid', '=', env.uid)
    #   ])
    #
    #   # Track who modified what and when
    #   for booking in bookings:
    #       print(f"{booking.booking_number}:")
    #       print(f"  Created: {booking.create_date} by {booking.create_uid.name}")
    #       print(f"  Modified: {booking.write_date} by {booking.write_uid.name}")
    #
    # WHY USEFUL:
    #   - Automatic audit trails (no manual tracking)
    #   - Debugging (who created this broken record?)
    #   - User activity reports
    #   - Data synchronization (sync records modified since last check)
    #   - Security investigations
    # ========================================================================

    # ========================================================================
    # ORM METHODS - CREATE OVERRIDE
    # ========================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to generate booking numbers.

        @api.model_create_multi EXPLAINED:
            - Batch creation optimization (Odoo 13+)
            - Receives list of value dictionaries
            - Creates multiple records in one transaction
            - More efficient than calling create() multiple times

        SEQUENCE GENERATION:
            1. Check if booking_number is 'New' or missing
            2. Call ir.sequence.next_by_code('service.booking')
            3. Returns next number: BOOK/2026/0001
            4. Update vals with generated number
            5. Call super().create() with updated vals

        WHY IN create() NOT IN defaults:
            - Ensures unique number even with batch operations
            - Handles race conditions via PostgreSQL sequence
            - Allows manual override in special cases

        CONCURRENCY SAFETY:
            - ir.sequence uses PostgreSQL SEQUENCE
            - Multiple users creating simultaneously get unique numbers
            - No gaps, no duplicates (unless sequence reset)
        """
        for vals in vals_list:
            if vals.get('booking_number', _('New')) == _('New'):
                vals['booking_number'] = self.env['ir.sequence'].next_by_code(
                    'service.booking'
                ) or _('New')

            # Auto-set amount from event's applicable price
            if 'event_id' in vals and 'amount' not in vals:
                event = self.env['service.event'].browse(vals['event_id'])
                booking_date = vals.get('booking_date') or fields.Date.context_today(self)
                # Convert string date to Date object if needed
                if isinstance(booking_date, str):
                    booking_date = fields.Date.to_date(booking_date)
                vals['amount'] = event.get_applicable_price(booking_date)

        return super().create(vals_list)

    # ========================================================================
    # WORKFLOW ACTIONS
    # ========================================================================

    def action_confirm(self):
        """
        Confirm the booking.

        WHY action_ PREFIX:
            - Odoo convention for button actions
            - Clearly indicates user-triggered workflow methods

        USAGE:
            - Called from button in form view
            - Can be called programmatically: booking.action_confirm()

        ENHANCEMENTS:
            - Validate event allows bookings
            - Auto-waitlist if capacity full
            - Check for duplicate bookings
        """
        for booking in self:
            # Validate event allows bookings
            allowed, reason = booking.event_id.check_booking_allowed()

            if not allowed:
                # Event is full - auto-waitlist instead of confirming
                if 'full capacity' in reason.lower():
                    booking.write({'state': 'waitlisted'})
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Added to Waitlist'),
                            'message': _(f'Booking {booking.booking_number} added to waitlist. '
                                       f'You are #{booking.waitlist_position} in line.'),
                            'type': 'warning',
                            'sticky': False,
                        }
                    }
                else:
                    raise ValidationError(reason)

            # Check for duplicate booking (same customer + event)
            duplicate = self.search([
                ('partner_id', '=', booking.partner_id.id),
                ('event_id', '=', booking.event_id.id),
                ('state', 'in', ['confirmed', 'done']),
                ('id', '!=', booking.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    f"Customer {booking.partner_id.name} already has a confirmed booking "
                    f"({duplicate.booking_number}) for event '{booking.event_id.name}'"
                )

            booking.write({'state': 'confirmed'})

    def action_done(self):
        """Mark booking as done (event completed)."""
        self.ensure_one()
        self.write({'state': 'done'})

    def action_cancel(self):
        """
        Cancel the booking.

        ENHANCEMENTS:
            - Promote from waitlist if spot opens
            - Track cancellation for metrics
        """
        for booking in self:
            was_confirmed = booking.state == 'confirmed'
            event = booking.event_id

            booking.write({'state': 'cancelled'})

            # If confirmed booking was cancelled, check waitlist
            if was_confirmed and event:
                event._promote_from_waitlist()

        return True

    def action_draft(self):
        """Reset to draft (for corrections)."""
        self.ensure_one()
        self.write({'state': 'draft'})

    # ========================================================================
    # BUSINESS HELPER METHODS
    # ========================================================================

    def action_promote_from_waitlist(self):
        """
        Manually promote this booking from waitlist to confirmed.

        USE CASE:
            - Admin manually promotes waitlisted customer
            - Overbook intentionally (e.g., expecting cancellations)

        VALIDATION:
            - Must be in waitlisted state
            - Event should have capacity (warning if not)
        """
        self.ensure_one()

        if self.state != 'waitlisted':
            raise ValidationError(
                f"Cannot promote booking {self.booking_number}: Not in waitlisted state"
            )

        # Check capacity (warning, not blocking)
        if self.event_id.capacity > 0:
            if self.event_id.booking_count_confirmed >= self.event_id.capacity:
                # Allow but warn
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Overbooking Warning'),
                        'message': _(
                            f'Event is at capacity ({self.event_id.capacity}). '
                            f'Promoting anyway (manual override).'
                        ),
                        'type': 'warning',
                        'sticky': True,
                    }
                }

        self.write({'state': 'confirmed'})
        return True

    def action_draft(self):
        """Reset to draft (for corrections)."""
        self.ensure_one()
        self.write({'state': 'draft'})

    # ========================================================================
    # CONSTRAINTS
    # ========================================================================

    @api.constrains('booking_date')
    def _check_booking_date(self):
        """
        Validate booking date is not in the past.

        @api.constrains EXPLAINED:
            - Python-level constraint (runs in application layer)
            - More flexible than SQL constraints
            - Can access related records, call methods, etc.
            - Triggered on create/write of specified fields

        USAGE:
            - Validates business rules
            - Raises ValidationError if check fails
            - Error message shown to user

        WHEN TO USE:
            - SQL constraints: Simple, single-field checks
            - Python constraints: Complex, multi-field/record validation
        """
        for booking in self:
            if booking.booking_date and booking.booking_date < fields.Date.context_today(self):
                raise ValidationError(_(
                    'Booking date cannot be in the past. '
                    'Please select today or a future date.'
                ))

    _sql_constraints = [
        (
            'positive_amount',
            'CHECK (amount >= 0)',
            'Booking amount must be positive or zero'
        ),
    ]

    # ========================================================================
    # ONCHANGE METHODS
    # ========================================================================

    @api.onchange('event_id')
    def _onchange_event_id(self):
        """
        Auto-populate fields when event is selected.

        @api.onchange EXPLAINED:
        ========================
        WHAT:
            Decorator that triggers a method when a field changes in the UI.

        WHY:
            - Improve user experience (auto-fill forms)
            - Show warnings/suggestions before saving
            - Update dependent fields dynamically

        HOW IT WORKS:
            1. User changes event_id in form view
            2. Odoo detects change (before save)
            3. Calls this method with current form values
            4. Method updates self with new values
            5. UI refreshes to show changes
            6. User can still edit before saving

        CRITICAL: Changes are NOT saved to database yet!
            - onchange updates form state only
            - User must click Save to persist

        ONCHANGE vs COMPUTE:
        ====================
        @api.onchange:
            ✅ Runs in UI before save
            ✅ User can override
            ✅ Can show warnings/messages
            ❌ Not triggered programmatically
            ✅ BEST FOR: User assistance, form auto-fill

        @api.compute:
            ✅ Runs on save and programmatically
            ❌ Readonly by default
            ✅ Can be stored
            ✅ Always recalculated
            ✅ BEST FOR: Calculated values, business logic

        RETURN VALUE:
        =============
        Can return dictionary with:
            - 'warning': Show popup message
            - 'domain': Filter related field options

        EXAMPLE RETURN:
            return {
                'warning': {
                    'title': 'Warning',
                    'message': 'Event is almost full!'
                },
                'domain': {
                    'partner_id': [('customer_rank', '>', 0)]
                }
            }
        """
        if self.event_id:
            # Auto-populate amount using applicable price (early bird + discount)
            booking_date = self.booking_date or fields.Date.context_today(self)
            self.amount = self.event_id.get_applicable_price(booking_date)

            # Check availability and warn if low
            if hasattr(self.event_id, 'available_seats'):
                if self.event_id.available_seats == 0:
                    return {
                        'warning': {
                            'title': _('Event Full'),
                            'message': _(
                                f"Event '{self.event_id.name}' is at full capacity "
                                f"({self.event_id.capacity} seats). "
                                f"This booking may be waitlisted."
                            )
                        }
                    }
                elif 0 < self.event_id.available_seats <= 5:
                    return {
                        'warning': {
                            'title': _('Low Availability'),
                            'message': _(
                                f"Only {self.event_id.available_seats} seats remaining "
                                f"for '{self.event_id.name}'."
                            )
                        }
                    }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Update form when customer changes.

        USAGE PATTERNS:
            - Could filter events based on customer preferences
            - Could apply customer-specific discounts
            - Could show customer's booking history

        DEMONSTRATION:
            This shows how to modify other fields based on partner selection.
        """
        if self.partner_id:
            # Example: Could apply customer-specific discount
            # if self.partner_id.is_vip:
            #     self.amount = self.amount * 0.9  # 10% VIP discount

            # Could set domain to filter events by customer preferences
            # customer_category = self.partner_id.preferred_category_id
            # return {'domain': {'event_id': [('category_id', '=', customer_category.id)]}}
            pass

    @api.onchange('booking_date')
    def _onchange_booking_date(self):
        """
        Validate and warn about booking date.

        DIFFERENCE FROM CONSTRAINT:
            @api.constrains: Blocks save with error
            @api.onchange: Shows warning, allows save

        USE CASE:
            Constraint: Hard rule (cannot save past dates)
            Onchange: Soft warning (can save weekend dates but warn)
        """
        if self.booking_date:
            # Warn if booking on weekend (example business rule)
            weekday = self.booking_date.weekday()  # Monday=0, Sunday=6
            if weekday in (5, 6):  # Saturday or Sunday
                return {
                    'warning': {
                        'title': _('Weekend Booking'),
                        'message': _(
                            'You are creating a booking on a weekend. '
                            'Please note that our office is closed on weekends.'
                        )
                    }
                }

    _sql_constraints = [
        (
            'positive_amount',
            'CHECK (amount >= 0)',
            'Booking amount must be positive or zero'
        ),
    ]
    # SQL constraint for simple amount validation
