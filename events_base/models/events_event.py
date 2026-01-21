from odoo import models, fields


class EventsEvent(models.Model):
    _name = 'events.event'
    _description = "Event"

    name = fields.Char(string="Event Name", required=True)
    image = fields.Image("Event Image")
    description = fields.Html(string="Description")
    price = fields.Float(string="Price", required=True)
    active = fields.Boolean(default=True)
    category_id = fields.Many2one('events.category', string="Category")
    tag_ids = fields.Many2many('events.tag', string="Tags")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    booking_ids = fields.One2many(string="Bookings", comodel_name='events.booking', inverse_name='event_id')
