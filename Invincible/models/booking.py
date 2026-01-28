
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InvincibleBooking(models.Model):
    _name = "invincible.booking"
    _description = "Event Booking"

    name = fields.Char(
        readonly=True
    )

    partner_id = fields.Many2one("res.partner", required=True)
    event_id = fields.Many2one("invincible.event", required=True)

    state = fields.Selection(
        default="draft"
    )

    booking_date = fields.Datetime(default=fields.Datetime.now)

    amount = fields.Float(
        compute="_compute_amount",
        store=True
    )

    company_id = fields.Many2one(
        related="event_id.company_id",
        store=True
    )


    @api.depends("event_id.price")
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.event_id.price

    @api.constrains("booking_date")
    def _check_past_date(self):
        for rec in self:
            if rec.booking_date < fields.Datetime.now():
                raise ValidationError("Cannot book past dates")

    # need to set sql constraints
    # _sql_constraints = [
    #     (
    #         "unique_partner_event",
    #         "unique(partner_id, event_id)",
    #         "You already booked this event."
    #     )
    # ]
