from odoo import fields, models


class Services(models.Model):
    _name = "quickbook.service"
    _description = "services related information"

    name = fields.Char(required=True)
    # help adds tooltip on that field and string gives name to field
    description = fields.Html(help="Description of the service")
    price = fields.Float(required=True)
    active = fields.Boolean(required=True)
    category_id = fields.Many2one("quickbook.category", string="Category")
    tag_ids = fields.Many2many("quickbook.tag", string="Tags")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    booking_ids = fields.One2many(
        "quickbook.booking", "service_id", string="Bookings"
    )
