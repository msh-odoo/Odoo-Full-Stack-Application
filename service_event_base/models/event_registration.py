from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    _name = 'event.registrations'
    _description = 'Event Registration'

    attendee_name = fields.Char(string='Attendee Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    service_id = fields.Many2one('event.management', string='Event Service', ondelete='cascade', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    booking_date = fields.Datetime(string='Booking Date', default=fields.Datetime.now)
    booking_amount = fields.Monetary(string='Booking Amount', currency_field='currency_id', compute='_compute_booking_amount', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='service_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', related='service_id.company_id', store=True, readonly=True)

    _booking_service_check = models.Constraint(
        'unique (service_id, partner_id)',
        "Each partner can register only once for the same event service."
    )

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
                raise ValidationError(_("Booking date cannot be in the past."))
