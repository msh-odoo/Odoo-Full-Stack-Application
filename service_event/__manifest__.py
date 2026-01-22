{
    'name': 'Service Event',
    'version': '1.0',
    'description': 'Service Event',
    'summary': 'Service Event',
    'author': 'Odoo',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/booking_sequence.xml',
        'views/service_event_views.xml',
        'views/service_event_booking.xml',
        'views/service_event_menus.xml',
    ],
    'demo': [],
    'application': True,
    'assets': {}
}
