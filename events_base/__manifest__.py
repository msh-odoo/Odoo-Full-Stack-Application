# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Events Base',
    'version': '0.1',
    'category': 'Marketing/Events',
    'summary': 'Base module for managing events',
    'description': """
Event Base
""",
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data':[
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/events_base_events_views.xml',
        'views/events_base_bookings_views.xml',
        'views/events_base_menus.xml',
    ],
    'application': True,
    'installable': True,
}
