from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    _name = 'event.registrations'
    _description = 'Event Registration'

    name = fields.Char('Name', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], 'Status', default='draft', required=True)
    active = fields.Boolean('Active', default=True)

    booking_date = fields.Datetime('Booking Date', default=fields.Datetime.now)
    booking_amount = fields.Monetary('Booking Amount', currency_field='currency_id', compute='_compute_booking_amount', store=True, readonly=True)

    service_id = fields.Many2one('event.service', 'Event Service', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', index=True)
    currency_id = fields.Many2one('res.currency', 'Currency', related='service_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', related='service_id.company_id', store=True, readonly=True)

    # Compute fields
    @api.depends('service_id')
    def _compute_booking_amount(self):
        for record in self:
            record.booking_amount = record.service_id.price

    # Python constrains
    @api.constrains('booking_date')
    def _check_booking_date(self):
        for record in self:
            if record.booking_date and record.booking_date < fields.Datetime.now():
                raise ValidationError(_("Booking date cannot be in the previous one."))
