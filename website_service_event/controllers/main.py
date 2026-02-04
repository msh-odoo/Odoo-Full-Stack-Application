from odoo.http import request
from odoo import http


class ServiceEventController(http.Controller):
    @http.route(["/service_event", '/service_event/page/<int:page>'], type="http", auth="public", website=True)
    def service_event_list(self, page=1, **kw):
        service_events = request.env['service.event'].search([("is_published", "=", True)])
        return request.render("website_service_event.service_event_listing_page", {
            "service_events": service_events,
            "length": len(service_events)
        })

    @http.route(['/service_event/<model("service.event"):service_event>'], type="http", auth="public", website=True)
    def service_event(self, service_event, **kw):
        service_event = request.env['service.event'].browse(service_event.id)
        return request.render("website_service_event.service_event_page", {
            "service_event": service_event
        })
