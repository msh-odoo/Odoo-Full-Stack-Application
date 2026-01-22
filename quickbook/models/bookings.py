from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Bookings(models.Model):
    _name = "quickbook.booking"
    _description = "Booking information for a service"
    _order = "booking_date desc"

    name = fields.Char(
        string="Booking Reference",
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    service_id = fields.Many2one("quickbook.service", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        required=True,
    )
    booking_date = fields.Datetime(required=True, default=fields.Datetime.now)
    quantity = fields.Integer(required=True)
    amount = fields.Float(compute="_compute_amount", store=True)
    company_id = fields.Many2one("res.company", required=True)

    @api.constrains("booking_date")
    def _check_booking_date(self):
        for rec in self:
            if rec.booking_date and rec.booking_date < fields.Datetime.now():
                raise ValidationError(
                    _("The booking with past booking data is not acceptable.")
                )

    _sql_constraints = [
        (
            "unique_partner_service",
            "unique(partner_id, service_id)",
            "A customer can book a service only once.",
        )
    ]

    @api.depends("service_id.price", "quantity")
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.service_id.price * rec.quantity

    @api.model
    def create(self, vals):
        vals["name"] = (
            self.env["ir.sequence"].next_by_code("quickbook.bookings") or "BOOKOR001"
        )
        vals.setdefault("state", "draft")
        return super().create(vals)

    @api.model
    def write(self, vals):
        for booking in self:
            if booking.state == "confirmed":
                raise UserError(_("Confirmed bookings cannot be modified."))
        return super().write(vals)

    @api.model
    def search(self, domain=None, offset=0, limit=None, order=None):
        domain = list(domain or [])
        # base.group_system is the Administrator group.
        if not self.env.user.has_group('base.group_system'):
            # Excludes records whose state is "cancelled"
            domain.append(('state', '!=', 'cancelled'))
        return super().search(domain, offset, limit, order)
