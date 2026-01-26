# -*- coding: utf-8 -*-
{
    'name': 'Service Event Website',
    'version': '1.0.0',
    'category': 'Website',
    'summary': 'Website and Portal integration for Service Event Booking System',
    'description': """
        Service Event Website Module
        ============================
        This module extends the base service event module with website and portal functionality.
        
        Features:
        - Public website pages for services/events
        - Portal pages for customer bookings
        - Website snippets for dynamic content
        - Snippet options and interactions
        - HTTP and JSON controllers
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'service_event_base',
        'website',
        'portal',
    ],
    'data': [
    ],
    'assets': {
        'web.assets_frontend': [
        ],
        'website.assets_wysiwyg': [
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
