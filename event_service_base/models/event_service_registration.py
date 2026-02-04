from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EventServiceRegistration(models.Model):
    _name = "event.service.registration"
    _description = "Event Service Registration"

    name = fields.Char(string="Event Name", readonly=True, copy=False)
    quantity = fields.Integer(string="Number of Attendees", default=1)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", readonly=True)
    amount = fields.Monetary(string="Total Amount", compute="_compute_amount", store=True, currency_field="currency_id")
    booking_date = fields.Datetime(string="Booking Date", default=fields.Datetime.now, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default = 'draft', readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", required=True, ondelete="restrict")
    service_id = fields.Many2one("event.service", string="Service", required=True, ondelete="restrict")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, ondelete="restrict")

    _unique_booking = models.Constraint(
        "unique(partner_id, service_id)",
        "You cannot register the same service twice.",
    )

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(
                    "Number of attendees must be greater than zero."
                )
            
    @api.depends('service_id.price', 'quantity')
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.service_id.price
    
    @api.constrains("company_id", "service_id")
    def _check_company_consistency(self):
        for record in self:
            if (
                record.service_id
                and record.service_id.company_id != record.company_id
            ):
                raise ValidationError(
                    "The service and the booking must belong to the same company."
                )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "event.service.registration"
                )
        return super().create(vals_list)

    @api.constrains("booking_date")
    def _check_booking_date(self):
        now = fields.Datetime.now()
        for record in self:
            if record.booking_date and record.booking_date < now:
                raise ValidationError(
                    "The booking date cannot be in the past."
                )
