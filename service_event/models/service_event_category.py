from odoo import fields, models


class ServiceEventCategory(models.Model):
    _name = 'service.event.category'
    _description = 'Service Event Category'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
