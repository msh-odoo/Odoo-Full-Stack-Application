from odoo import fields, models


class ServiceTags(models.Model):
    _name = "quickbook.tag"
    _description = "Tags"
    _rec_name = "name"

    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color", default=0, help="Tag color")
    description = fields.Text(string="Description", help="Tag description")
