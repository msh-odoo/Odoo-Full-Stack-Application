from odoo import http
from odoo.http import request
from math import ceil


class QuickBookWebsite(http.Controller):
    _services_per_page = 4

    @http.route(
        ["/services", "/services/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
    )
    def services_listing(self, page=1, **kwargs):
        Service = request.env["quickbook.service"]
        domain = [("active", "=", True)]
        offset = (page - 1) * self._services_per_page
        services = Service.search(domain, limit=self._services_per_page, offset=offset)
        total_services = Service.search_count(domain)
        total_pages = ceil(total_services / self._services_per_page)
        pager = request.website.pager(
            url="/services",
            total=total_pages,
            page=page,
            step=1,  # Number of pages to show in the pager
            scope=5,  # Number of pages visible in pager around current page
        )
        return request.render(
            "quickbook_website.services_list_website",
            {
                "services": services,
                "pager": pager,
                "total_properties": total_services,
                "page": page,
                "total_pages": total_pages,
            },
        )

    @http.route(
        ["/services/<int:service_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def services_detail(self, service_id, **kwargs):
        service_details = request.env["quickbook.service"].browse(service_id)
        if service_details.exists():
            return request.render(
                "quickbook_website.services_detail_website",
                {"service": service_details},
            )
        else:
            request.redirect("/services")
