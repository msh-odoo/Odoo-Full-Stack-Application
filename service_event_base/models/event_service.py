from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventService(models.Model):
    _name = 'event.service'
    _description = 'Event Management Service'

    name = fields.Char('Event Name', required=True)
    description = fields.Html('Description')
    price = fields.Monetary('Price', currency_field='currency_id')
    active = fields.Boolean('Active', default=True)
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    event_type_id = fields.Many2one('event.type', 'Event Type', ondelete='set null', index=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    booking_ids = fields.One2many('event.registrations', 'service_id', 'Bookings')

    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.company_id.currency_id, readonly=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date <= record.start_date:
                raise ValidationError(_('End date must be after start date.'))
    
    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price < 0:
                raise ValidationError(_('Price must be zero or positive.'))
    
    @api.onchange('price')
    def _onchange_price(self):
        if self.price and self.price < 0:
            self.price = 0
            return {
                'warning': {
                    'title': _('Invalid Price'),
                    'message': _('Price cannot be negative.'),
                }
            }
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        #logic here write
        return records
