# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare

class EventServices(models.Model):
    _name = "event.services"
    _description = "Event Services"

    name = fields.Char("Name of the services", required=True, translate=True)
    description = fields.Html("description", help="full description with event", translate=True)
    price = fields.Float("Price", default="0", help="price per person")
    max_seat = fields.Integer("Maximum Seats", required=True, help="maximum number of participats")
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    # RELATIONAL FIELDS
    category_id = fields.Many2one('event.tag', 'category')
    tag_ids = fields.Many2many('event.tag', 'Tags')
    company_id = fields.Many2one('res.company', 'Company', store=True)
    # booking_ids = fields.One2many('event.registation', 'Registration')

    # Any depend decorater define here

    #Define Python Constrains
    @api.constrains('max_seats')
    def _check_max_seats(self):
        """Validate: max_seats must be positive"""
        for record in self:
            if record.max_seats < 1:
                raise ValidationError(  # noqa: F821
                    _('Maximum seats must be at least 1!')
                )

    @api.constrains('price')
    def _check_price(self):
        """Validate: price cannot be negative"""
        for record in self:
            if float_compare(record.price, 0.0, precision_digits=2) < 0:  # noqa: F821
                raise ValidationError(  # noqa: F821
                    _('Price cannot be negative!')
                )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate: end_date must be after start_date"""
        for record in self:
            if record.end_date and record.start_date:
                if record.end_date <= record.start_date:
                    raise ValidationError(  # noqa: F821
                        _('End date (%s) must be after start date (%s)!') % (
                            record.end_date, record.start_date
                        )
                    )
