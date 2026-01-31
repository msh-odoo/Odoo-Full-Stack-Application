# -*- coding: utf-8 -*-
# Service Event Website Module Manifest
#
# ARCHITECTURE:
#     This is the WEBSITE module, separated from service_event_base.
#     - service_event_base: Core business logic (models, security, ORM)
#     - service_event_website: Web pages, controllers, portal (THIS MODULE)
#
# WHY SEPARATE:
#     - Clean separation of concerns (backend vs frontend)
#     - service_event_base can be used without website (API, mobile, etc.)
#     - Easier to maintain and test
#     - Follows Odoo best practices (sale vs sale_management pattern)
#
# DEPENDENCIES:
#     - service_event_base: Our core business logic
#     - website: Odoo's website builder framework
#     - portal: Customer portal functionality

{
    'name': 'Service Event Website',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Website pages and controllers for service event booking system',
    'description': """
        Service Event Website Module
        =============================

        Extends service_event_base with website functionality.

        Features:
        ---------
        * Public event listing page
        * Event detail pages with booking form
        * Online booking submission
        * Customer portal for booking management
        * SEO-optimized (sitemap, meta tags)
        * Responsive design (Bootstrap 5)

        Controllers:
        ------------
        * /events - Event listing (GET, auth=public)
        * /events/<model("service.event"):event> - Event detail (GET, auth=public)
        * /events/book - Booking submission (POST, auth=user, CSRF protected)
        * Sitemap integration for search engines

        Technical Highlights:
        ---------------------
        * Demonstrates HTTP routing (GET/POST)
        * Model converters for clean URLs
        * CSRF protection on forms
        * QWeb template rendering
        * Bootstrap 5 responsive design
        * Portal integration
    """,

    'author': 'Odoo Full-Stack Development Team',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'service_event_base',  # Our core business logic
        'website',             # Odoo website builder
        'portal',              # Customer portal
    ],

    # Data files
    'data': [
        # Security
        'security/portal_security.xml',
        # Templates
        'views/website_templates.xml',
        'views/portal_templates.xml',
    ],

    # Assets (JS/CSS)
    'assets': {
        'web.assets_frontend': [
            # Future: custom CSS/JS for event pages
        ],
    },

    # Module flags
    'installable': True,
    'application': False,  # This is an extension, not standalone
    'auto_install': False,
}
