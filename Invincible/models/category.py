
from odoo import models, fields

class InvincibleCategory(models.Model):
    _name = "invincible.category"
    _description = "Event Category"

    name = fields.Char(required=True)
