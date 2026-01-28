
from odoo import models, fields, api

class InvincibleEvent(models.Model):
    _name = "invincible.event"
    _description = "Invincible NGO Event"
    _rec_name = "name"

    name = fields.Char(required=True)
    description = fields.Html()
    price = fields.Float()
    active = fields.Boolean(default=True)

    category_id = fields.Many2one("invincible.category")
    tag_ids = fields.Many2many("invincible.tag")

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company
    )

    booking_ids = fields.One2many(
        "invincible.booking", "event_id"
    )

    is_expensive = fields.Boolean(
        compute="_compute_is_expensive",
        search="_search_is_expensive",
        inverse="_inverse_is_expensive",
    )

    @api.depends('price')
    def _compute_is_expensive(self):
        for rec in self:
            rec.is_expensive = rec.price > 1000

    def _search_is_expensive(self, operator, value):
        return [("price", ">", 1000)] if value else [("price", "<=", 1000)]

    def _inverse_is_expensive(self):
        for rec in self:
            if rec.is_expensive:
                rec.price = 1010
