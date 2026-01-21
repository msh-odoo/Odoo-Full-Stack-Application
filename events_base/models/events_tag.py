from odoo import models, fields


class EventsTag(models.Model):
    _name = 'events.tag'
    _description = "Events Tag"

    name = fields.Char(string="Tag Name", required=True)
