from odoo import api, fields, models, _


class EventService(models.Model):
    _name = 'event.management'
    _description = 'Event Management Service'
    
    name = fields.Char(string='Event Name', required=True)
    description = fields.Html(string='Description')
    price = fields.Monetary(string='Price', currency_field='currency_id')
    active = fields.Boolean(string='Active', default=True)
    # Many2one relationship to event type from odoo standard event module
    event_type_id = fields.Many2one('event.type', string='Event Type', ondelete='set null', index=True)
    tag_ids = fields.Many2many('event.tag', string='Tags', compute='_compute_tag_ids')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    booking_ids = fields.One2many('event.registrations', 'service_id', string='Bookings')
    # You are never going to use multi-currency in a single company or change it either.
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.company_id.currency_id, readonly=True)

    @api.depends('event_type_id')
    def _compute_tag_ids(self):
        """If you are changing the event type, also your tags are empty. In that
        Case just assign the tags from event_type_id to current record. Already
        done in standard event module."""
        for record in self:
            if not record.tag_ids and record.event_type_id:
                record.tag_ids = record.event_type_id.tag_ids
