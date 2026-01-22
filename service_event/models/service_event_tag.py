from odoo import fields, models


class ServiceEventTag(models.Model):
    _name = 'service.event.tag'
    _description = 'Service Event Tag'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index', default=0)
