from odoo import models, fields


class Service(models.Model):
    _name = 'ods.service'
    _description = 'Single Service Offering Bookable by Customers (e.g., Plumbing, AC Servicing, Cleaning)'

    name = fields.Char(string='Service Name', required=True)
    description = fields.Text(string='Description')
    duration = fields.Integer(string='Duration (in minutes)', required=True)
    price = fields.Monetary(required=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
    )