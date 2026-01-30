from odoo import http


class Main(http.Controller):
    @http.route('/ods/hello', auth='public')
    def hello(self, **kw):
        return "Hello, world"

