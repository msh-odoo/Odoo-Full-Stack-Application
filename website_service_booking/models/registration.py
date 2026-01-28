from odoo import fields, models


class Registration(models.Model):
    _name = "registration"
    _description = "Service Booking Registration Model"

    name = fields.Char()
    quantity = fields.Integer(string="Attendees Count", default=1)
    amount = fields.Float(string="Total Amount", compute="_compute_amount", store=True)
    # should we use fields.Datetime.now()  or lambda self: fields.Datetime.now() ?
    booking_date = fields.Datetime(
        string="Booking Date", default=fields.Datetime.now(), required=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        default="draft",
    )
