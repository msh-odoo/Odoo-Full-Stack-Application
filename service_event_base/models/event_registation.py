# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class EventRegistation(models.Model):
    _name = "event.registation"
    _description = "Event Registation "

    name = fields.Char("Name of the event", required=True, translate=true)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
        ],
        'Status',
        help='Registration status'
    )
    booking_date = fields.Datetime("Booking Dtae")
    seats_count = fields.Integer(string='Number of Seats', required=True, help='Number of seats to reserve')

    partner_id = fields.Many2one('res.partner', help="person registering for event")
    services_id = field.Many2one('event.service', help="Event big registering for")
    company_id = fields.Many2one('res.company')

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    unit_price = fields.Float(related='service_id.price', string='Unit Price')

    # COMPUTED FIELDS HERE
    amount = fields.Monetary(string='Total Amount', compute='_compute_amount', help='Total registration cost')

    #depends decorator Here
    @api.depends('unit_price', 'seats_count')
    def _compute_amount(self):
        """Compute total amount"""
        for record in self:
            record.amount = record.unit_price * record.seats_count

    #onchange decorator here
    @api.onchange('seats_count')
    def _onchange_seats_count(self):
        """Validate seats count"""
        if self.seats_count < 1:
            self.seats_count = 1
            return {
                'warning': {
                    'title': _('Invalid Seats'),
                    'message': _('Seats count must be at least 1'),
                }
            }
        # Check availability for seats
        if self.service_id and self.seats_count > self.service_id.seats_available:
            return {
                'warning': {
                    'title': _('Insufficient Seats'),
                    'message': _(
                        'Only %s seats available, we have to selected %s'
                    ) % (self.service_id.seats_available, self.seats_count),
                }
            }
