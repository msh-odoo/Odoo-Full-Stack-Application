{
    'name': "On Demand Services (ODS)",
    'summary': "Manage and book on-demand home services such as plumbing, repairs, and maintenance.",
    'description': """
        On Demand Services (ODS) allows you to manage and offer on-demand home and field services
        directly from Odoo.

        You can define multiple service offerings (such as plumbing, repairs, cleaning, and maintenance)
        from the backend, onboard and manage service professionals for each service, and control pricing,
        availability, and service details.

        Customers can then browse and book these services, while administrators can track bookings,
        assign professionals, and monitor service operations from a single system.
    """,

    'author': "Arib Ansari",
    'license': 'LGPL-3',

    'category': 'Learning',
    'version': '0.1',
    'application': True,
    'sequence': 1,

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/service_views.xml',
        'views/menus.xml',
    ],
}
