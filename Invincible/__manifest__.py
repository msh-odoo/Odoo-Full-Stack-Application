
{
    "name": "Invincible NGO – Event Base",
    "version": "1.0",
    "category": "Event Booking",
    "depends": ["base", "mail", "website"],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        
        # "wizards/add_event.xml",

        "views/booking_views.xml",
        "views/event_views.xml",
        "views/event_menus.xml",
        "views/event_controller.xml",
    ],
    'author': "Odoo",
    'sequence':'1',
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
