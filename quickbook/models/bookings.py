from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import timedelta


class Bookings(models.Model):
    _name = "quickbook.booking"
    _description = "Booking information for a service"
    _order = "booking_date desc"

    name = fields.Char(
        string="Booking Reference",
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    service_id = fields.Many2one(
        "quickbook.service",
        required=True,
        domain=[("active", "=", True)],
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
            ("completed", "Completed"),
        ],
        default="draft",
    )
    booking_date = fields.Datetime(required=True, default=fields.Datetime.now)
    quantity = fields.Integer(required=True, default=1)
    amount = fields.Float(compute="_compute_amount", store=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned Staff",
        default=lambda self: self.env.user,
        help="Staff member handling this booking",
    )
    notes = fields.Text(
        string="Special Requests",
        help="Any special notes or requests from the customer",
    )
    review_rating = fields.Selection(
        [
            ("1", "1 - Poor"),
            ("2", "2 - Fair"),
            ("3", "3 - Good"),
            ("4", "4 - Very Good"),
            ("5", "5 - Excellent"),
        ],
        string="Rating",
        help="Customer rating after service completion",
    )
    review_comment = fields.Text(
        string="Review Comment", help="Customer review or feedback"
    )
    overdue_days = fields.Integer(
        string="Overdue (Days)",
        compute="_compute_overdue_days",
        inverse="_inverse_overdue_days",
        search="_search_overdue_days",
    )
    available_slots = fields.Integer(
        string="Available Slots",
        compute="_compute_available_slots",
        store=False,
        help="Number of available slots for this service at the selected date and time",
    )

    _sql_constraints = [
        (
            "unique_partner_service",
            "unique(partner_id, service_id)",
            "A customer can book a service only once.",
        )
    ]

    @api.depends("booking_date", "state")
    def _compute_overdue_days(self):
        for booking in self:
            if booking.state != "cancelled" and booking.booking_date:
                days = (fields.Datetime.now() - booking.booking_date).days
                booking.overdue_days = max(days, 0)

    @api.depends("service_id.capacity", "service_id.duration", "booking_date")
    def _compute_available_slots(self):
        # Compute available slots at the selected date and time.
        for booking in self:
            capacity = booking.service_id.capacity
            duration = booking.service_id.duration
            booking_start = booking.booking_date
            booking_end = booking_start + timedelta(hours=duration)

            # Count confirmed bookings that overlap with this time slot
            overlapping_bookings = self.env["quickbook.booking"].search_count(
                [
                    ("service_id", "=", booking.service_id.id),
                    ("state", "=", "confirmed"),
                    ("id", "!=", booking.id),  # Exclude current booking
                    ("booking_date", "<", booking_end),  # Booking starts before our end
                    (
                        "booking_date",
                        ">=",
                        booking_start - timedelta(hours=duration),
                    ),  # Booking ends after our start
                ]
            )
            booking.available_slots = max(capacity - overlapping_bookings, 0)

    @api.constrains("service_id", "booking_date")
    def _check_available_slots(self):
        for booking in self:
            if booking.available_slots <= 0:
                raise ValidationError(
                    _("No available slots for this service at the selected time.")
                )

    def _search_overdue_days(self, operator, value):
        overdue_value = fields.Datetime.now() - timedelta(days=value)
        # Domains must be list of tuple
        if operator in (">", ">="):
            return [("booking_date", "<", overdue_value)]
        elif operator in ("<", "<="):
            return [("booking_date", ">=", overdue_value)]
        elif operator == "=":
            return [("booking_date", "=", overdue_value)]
        else:
            return []

    @api.depends("overdue_days")
    def _inverse_overdue_days(self):
        for booking in self:
            if booking.overdue_days > 0:
                booking.booking_date = fields.Datetime.now() - timedelta(
                    days=booking.overdue_days
                )

    @api.constrains("quantity")
    def _check_quantity(self):
        for booking in self:
            if booking.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero"))

    @api.constrains("booking_date")
    def _check_booking_date(self):
        for rec in self:
            if rec.booking_date:
                # Use context_timestamp to handle timezone-aware comparison
                now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
                booking_datetime = fields.Datetime.context_timestamp(self, rec.booking_date)
                if booking_datetime < now:
                    raise ValidationError(
                        _("The booking with past booking data is not acceptable.")
                    )

    @api.depends("service_id.price", "quantity")
    def _compute_amount(self):
        for rec in self:
            price = rec.service_id.price
            if float_compare(price, 0.0, precision_digits=2) > 0:
                rec.amount = price * rec.quantity
            else:
                rec.amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("quickbook.bookings") or "BKOR001"
            )
            # vals.setdefault("state", "draft")
        return super().create(vals_list)

    def write(self, vals):
        # Fields that are allowed to be edited after confirmation
        allowed_fields = {"review_rating", "review_comment", "state"}
        for booking in self:
            if booking.state in ("completed", "cancelled"):
                raise UserError(
                    _(
                        "No changes are allowed once the booking is completed or cancelled."
                    )
                )
            if booking.state == "confirmed" and not set(vals.keys()).issubset(
                allowed_fields
            ):
                raise UserError(
                    _(
                        "Only review fields can be edited after confirmation.\n"
                        "Allowed fields: Rating and Review Comment."
                    )
                )

        return super().write(vals)

    def unlink(self):
        # Prevent deletion of confirmed bookings
        for booking in self:
            if booking.state in ("confirmed", "completed"):
                raise UserError(_("Cannot delete confirmed or completed bookings."))
        return super().unlink()

    @api.model
    def search(self, domain=None, offset=0, limit=None, order=None):
        domain = list(domain or [])
        # base.group_system is the Administrator group.
        if not self.env.user.has_group("base.group_system"):
            # Excludes records whose state is "cancelled"
            domain.append(("state", "!=", "cancelled"))
        return super().search(domain, offset, limit, order)
