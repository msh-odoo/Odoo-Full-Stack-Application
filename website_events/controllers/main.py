from odoo import http
from odoo.http import request

class WebsiteEventsController(http.Controller):
    @http.route(['/events-list', '/events-list/page/<int:page>'], type='http', auth="public", website=True,)
    def events_list(self, page=1, **kwargs):
        Events = request.env['events.event']
        domain = [('website_published', '=', True)]
        step = 9
        total_count = Events.search_count(domain)
        events = Events.search(domain, offset=(page - 1) * step, limit=step)
        pager = request.website.pager(
            url="/events-list",
            url_args=kwargs,
            total=total_count,
            page=page,
            step=step,
            scope=5
        )
        values = {
            'pager': pager,
            'events': events,
        }
        return request.render('website_events.events_list_page', values)
