from odoo import fields, models


class EventService(models.Model):
    _name = "event.service"
    _description = "Event Service"

    name = fields.Char(string="Name", required=True)
    description = fields.Html(string="Description")
    price = fields.Float(string="Price", default=0.0)
    active = fields.Boolean(string="Active", default=True)
    category_id = fields.Many2one("event.service.category", string="Category")
    tag_ids = fields.Many2many("event.service.tag", string="Tags")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    booking_ids = fields.One2many("event.service.registration", "service_id", string="Bookings")

class EventServiceCategory(models.Model):
    _name = "event.service.category"
    _description = "Event Service Category"

    name = fields.Char(string="Name", required=True)

class EventServiceTag(models.Model):
    _name = "event.service.tag"
    _description = "Event Service Tag"

    name = fields.Char(string="Name", required=True)
