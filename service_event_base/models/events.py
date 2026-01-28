from odoo import fields, models


class Events(models.Model):
    _name = 'events'
    _description = 'Events Service Base Model'

    name = fields.Char(string="Event Name", required=True)
    description = fields.Html(string="Event Description")
    price = fields.Float(string="Event Price")
    active = fields.Boolean(string="Is Active", default=True)
