{
    'name': 'Service Event Base',
    'version': '1.0.0',
    'summary': 'Base module for service event management',
    'description': 'This module provides the foundational models and views for managing service events within the Odoo framework.',
    'category': 'Services',
    'depends': ['base', 'mail', 'event'],
    'data': [
        'views/event_service_menu_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'author': 'Garvish',
    'license': 'LGPL-3',
}
