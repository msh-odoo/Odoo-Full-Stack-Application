from odoo import api, fields, models


class ServiceEventBooking(models.Model):
    _name = 'service.event.booking'
    _description = 'Service Event Booking'
    _order = 'id desc'

    name = fields.Char(string='Name', readonly=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    service_id = fields.Many2one('service.event', string='Service', required=True)
    quantity = fields.Integer(string='No. of Passes', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft')
    booking_date = fields.Date(string='Date', required=True)
    amount = fields.Float(string='Amount', compute="_compute_amount", store=True)
    active = fields.Boolean(string='Active', default=True)
    tag_id = fields.Many2one('service.event.tag', string='Tag')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.constrains('booking_date')
    def _validate_booking_date(self):
        for record in self:
            if record.booking_date < fields.Date.today():
                raise ValueError('Booking date cannot be in the past!')

    _unique_booking = models.Constraint(
        'unique (partner_id, service_id)',
        'Booking already exists with the same partner and service!',
    )

    @api.depends('service_id', 'quantity')
    def _compute_amount(self):
        for record in self:
            record.amount = record.service_id.price * record.quantity


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('service.event.booking')
        return super().create(vals_list)
