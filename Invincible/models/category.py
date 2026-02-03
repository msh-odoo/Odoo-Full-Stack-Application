
from odoo import models, fields

class InvincibleCategory(models.Model):
    _name = "invincible.event.category"
    _description = "Event Category"

    name = fields.Char(required=True)
