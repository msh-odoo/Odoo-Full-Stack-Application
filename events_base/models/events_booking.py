from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class EventsBooking(models.Model):
    _name = 'events.booking'
    _description = 'Event Booking'

    name = fields.Char(string="Name", copy=False, required=True, default=lambda self: self.env._("New"), readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    event_id = fields.Many2one('events.event', string="Event", required=True)
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft','Draft'),
            ('confirmed','Confirmed'),
            ('cancelled','Cancelled'),
        ],
        required=True,
        copy=False,
        default='draft'
    )
    quantity = fields.Integer(string="Quantity", required=True, default=1)
    booking_date = fields.Datetime("Booking Date", required=True)
    amount = fields.Float(string="Amount", compute='_compute_booking_amount', store=True)
    company_id = fields.Many2one('res.company', string="Company", related='event_id.company_id', store=True)
    is_expensive = fields.Boolean(string="Is Expensive?", compute='_compute_is_expensive',search='_search_is_expensive', inverse='_inverse_is_expensive')

    _unique_booking_partner_event = models.Constraint(
        'UNIQUE(partner_id, event_id)',
        'A partner can only have one booking per event.'
    )

    @api.depends('event_id.price', 'quantity')
    def _compute_booking_amount(self):
        for booking in self:
            booking.amount = booking.event_id.price * booking.quantity

    @api.depends('amount')
    def _compute_is_expensive(self):
        for booking in self:
            booking.is_expensive = booking.amount >= 2000

    def _inverse_is_expensive(self):
        for booking in self:
            if booking.is_expensive:
                booking.amount = 2000

    def _search_is_expensive(self, operator, value):
        if operator != 'in':
            return NotImplemented
        return [('amount', '>=', 2000)]

    @api.constrains('booking_date')
    def _check_booking_date_not_in_past(self):
        for booking in self:
            if booking.booking_date < fields.Datetime.now():
                raise ValidationError(self.env._("The booking date cannot be in the past."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', self.env._("New")) == self.env._("New"):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['booking_date'])
                ) if 'booking_date' in vals else None
                vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
                    'events.booking', sequence_date=seq_date) or self.env._("New")
        return super().create(vals_list)

    def write(self, vals):
        for booking in self:
            if booking.state == "confirmed":
                raise UserError(self.env._("You can't make changes after confirming booking"))
        return super().write(vals)
