# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class InvincibleEventController(http.Controller):

    # simple homepage – event listing with pagination
    @http.route(['/ngo/events'], type="http",website=True, auth='public')
    def event_controller(self, **kwargs):
        print("-----------------------")
        events = request.env['invincible.event'].sudo().search([])
        return request.render("invincible.ngo_event_list", {
            'events': events,
        })

    # # event detail page
    # @http.route(
    #     '/event/<int:event_id>',
    #     type='http',
    #     auth='public',
    #     website=True
    # )
    # def event_details(self, event_id):
    #     event = request.env['invincible.event'].sudo().browse(event_id)

    #     return request.render("invincible_event_website.view_event_form", {
    #         'event': event,
    #     })


    # # static info page (kept as-is, renamed context)
    # @http.route(
    #     ['/invincible/about'],
    #     type='http',
    #     auth="public",
    #     website=True,
    #     sitemap=False
    # )
    # def invincible_about(self):
    #     return request.render("invincible_event_website.invincible_about", {})
