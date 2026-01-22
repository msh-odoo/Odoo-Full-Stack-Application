from odoo import _, fields, models
from odoo.exceptions import UserError


class Services(models.Model):
    _name = "quickbook.service"
    _description = "services related information"

    name = fields.Char(required=True)
    # help adds tooltip on that field and string gives name to field
    description = fields.Html(help="Description of the service")
    price = fields.Float(required=True)
    active = fields.Boolean(required=True, default=True)
    category_id = fields.Many2one("quickbook.category", string="Category")
    tag_ids = fields.Many2many("quickbook.tag", string="Tags")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    booking_ids = fields.One2many("quickbook.booking", "service_id", string="Bookings")
    capacity = fields.Integer(
        string="Service Capacity",
        required=True,
        default=1,
        help="Total number of people available for this service at any given time slot",
    )
    duration = fields.Float(
        string="Service Duration (Hours)",
        required=True,
        default=1.0,
        help="Duration of service in hours",
    )

    def write(self, vals):
        # Override write to prevent price changes if active bookings exist
        if "price" in vals:
            for service in self:
                active_bookings_count = self.env["quickbook.booking"].search_count(
                    [
                        ("service_id", "=", service.id),
                        ("state", "in", ["draft", "confirmed"]),
                    ]
                )
                if active_bookings_count > 0:
                    raise UserError(_("Cannot modify price as it has active bookings."))
        return super().write(vals)
