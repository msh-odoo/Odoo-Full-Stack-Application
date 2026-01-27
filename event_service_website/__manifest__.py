{
    'name': 'Event Service Website',
    'summary': 'Manage event services and customer bookings',
    'description': """
- Definition of event services with pricing
- Service categories and tags
- Customer registrations for services
- Core business rules and validations for bookings

""",
    'version': '1.0',
    'depends': ['event_service_base', 'website', 'portal'],
    'author': 'Dhruv',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
