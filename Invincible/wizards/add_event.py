# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventBookingWizard(models.TransientModel):
    _name = 'invincible.event.booking.wizard'
    _description = 'Event Booking Wizard'

    partner_id = fields.Many2one(
        'res.partner',
        string="Participant",
        required=True
    )

    participants = fields.Integer(
        string="Number of Participants",
        default=1,
        required=True
    )

    booking_date = fields.Datetime(
        string="Booking Date",
        default=fields.Datetime.now,
        required=True
    )

    def action_create_booking(self):
        active_event_ids = self.env.context.get('active_ids', [])
        if not active_event_ids:
            raise UserError(_("No events selected."))

        events = self.env['invincible.event'].browse(active_event_ids)

        booking_vals = []
        for event in events:
            booking_vals.append({
                'partner_id': self.partner_id.id,
                'event_id': event.id,
                'participants': self.participants,
                'booking_date': self.booking_date,
            })

        self.env['invincible.booking'].create(booking_vals)

        return {'type': 'ir.actions.act_window_close'}
