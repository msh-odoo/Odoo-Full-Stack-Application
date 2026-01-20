# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class EventCategory(models.Model):
    _name = "event.category"
    _description = "Event category"

    name = fields.Char(string="Category Name", required=True)
    description = fields.Char(string='Description')
    active = fields.Boolean(default=True, help='Uncheck to archive the category')
