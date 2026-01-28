
{
    "name": "Invincible NGO – Event Base",
    "version": "1.0",
    "category": "Event Booking",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",

        "views/event_views.xml",
        "views/event_menus.xml",
    ],
    'author': "Odoo",
    'sequence':'1',
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
