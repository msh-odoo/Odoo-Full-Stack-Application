# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class EventTag(models.Model):
    _name = "event.tag"
    _description = "Event Tag "

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string='Color Index',default=0,help='Color for tag display')

    event_count = fields.Integer(string='Events Count',help='Number of events with this tag')

    @api.constrains('color')
    def _check_color(self):
        """Validate color index range"""
        for record in self:
            if record.color < 0 or record.color > 11:
                raise ValidationError(
                    _('Color index must be between 0 and 11!')
                )

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 
         'Tag name must be unique!'),
    ]
    