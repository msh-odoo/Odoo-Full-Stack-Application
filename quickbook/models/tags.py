from odoo import fields, models


class ServiceTags(models.Model):
    _name = "quickbook.tag"
    _description = "Tags"

    name = fields.Char(string="Tag", required=True)
