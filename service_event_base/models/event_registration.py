from odoo import api, fields, models, _


class EventRegistration(models.Model):
    _name = 'event.registrations'
    _description = 'Event Registration'

    attendee_name = fields.Char(string='Attendee Name', required=True)
    service_id = fields.Many2one(
        'event.management', string='Event Service',
        ondelete='cascade', required=True
    )
