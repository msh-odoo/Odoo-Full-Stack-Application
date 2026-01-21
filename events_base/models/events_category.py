from odoo import models, fields


class EventsCategory(models.Model):
    _name = 'events.category'
    _description = "Events Category"

    name = fields.Char(string="Category Name", required=True)
