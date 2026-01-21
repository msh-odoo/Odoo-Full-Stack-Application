from odoo import models, fields


class EventsEvent(models.Model):
    _inherit = 'events.event'

    website_published = fields.Boolean("Publish on website ?")
