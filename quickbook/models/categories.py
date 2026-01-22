from odoo import fields, models


class Categories(models.Model):
    _name = "quickbook.category"
    _description = "Categories"

    name = fields.Char(string="Category", required=True)
