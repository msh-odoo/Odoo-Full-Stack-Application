from odoo import api, fields, models


class ServiceEvent(models.Model):
    _name = 'service.event'
    _inherit = ['mail.thread']
    _description = 'Service Event'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True, tracking=True)
    image = fields.Image(string='Image')
    description = fields.Text(string='Description')
    price = fields.Float(string='Price', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    category_id = fields.Many2one('service.event.category', string='Category', required=True)
    tag_ids = fields.Many2many('service.event.tag', string='Tags')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    booking_ids = fields.One2many('service.event.booking', 'service_id', string='Bookings')
    is_published = fields.Boolean(string='Published', default=False)

    def action_toggle_is_published(self):
        """ Toggle the field `is_published`.

        :return: None
        """
        self.is_published = not self.is_published
