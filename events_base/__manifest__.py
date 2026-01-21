# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Events Base',
    'summary': 'Base module for managing events',
    'version': '0.1',
    'description': """
Event Base
""",
    'installable': True,
    'application': True,
    'depends': ['base'],
    'data':[
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/events_base_events_views.xml',
        'views/events_base_bookings_views.xml',
        'views/events_base_menus.xml',
    ],
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
