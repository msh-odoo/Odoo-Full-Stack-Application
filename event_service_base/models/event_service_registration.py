from community.odoo import api, fields, models


class EventServiceRegistration(models.Model):
    _name = "event.service.registration"
    _description = "Event Service Registration"

    name = fields.Char(string="Event Name", readonly=True, copy=False)
    quantity = fields.Integer(string="Number of Attendees", default=1)
    amount = fields.Float(string="Total Amount", compute="_compute_amount", store=True)
    booking_date = fields.Datetime(string="Booking Date", default=fields.Datetime.now, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default = 'draft')
    partner_id = fields.Many2one("res.partner", string="Partner", required=True, ondelete="cascade")
    service_id = fields.Many2one("event.service", string="Service", required=True, ondelete="restrict")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, ondelete="restrict")

    @api.depends('service_id.price', 'quantity')
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.service_id.price

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code("event.service.registration")
        return super().create(vals_list)
