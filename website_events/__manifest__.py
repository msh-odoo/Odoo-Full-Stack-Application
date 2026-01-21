{
    'name': "website_events",
    'version': '0.1',
    'category': 'Marketing/Events',
    'summary': "Integrate Events with the website",
    'description': """
Website Events
""",
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'events_base'],
    'data': [
        'views/events_list_templates.xml',
    ],
    'demo': [
        'demo/events_tag_demo.xml',
        'demo/events_event_demo.xml',
    ],
}
