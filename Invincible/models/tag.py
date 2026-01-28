
from odoo import models, fields

class InvincibleTag(models.Model):
    _name = "invincible.tag"
    _description = "Event Tag"

    name = fields.Char(required=True)
