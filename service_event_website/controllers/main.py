# -*- coding: utf-8 -*-
"""
Service Event Website Controllers

This module demonstrates Odoo's HTTP routing system for website pages.

ODOO HTTP ROUTING CONCEPTS:
===========================

1. ROUTE DECORATOR (@http.route)
   - Defines URL patterns and HTTP methods
   - Configures authentication and website integration
   - Maps URLs to Python methods

2. HTTP METHODS:
   - GET: Retrieve/display data (idempotent, cacheable)
   - POST: Submit/create data (non-idempotent, not cacheable)

3. AUTH TYPES:
   - auth='public': Anyone can access (even non-logged-in visitors)
   - auth='user': Requires logged-in user (portal or internal)
   - auth='admin': Requires internal user (backend access)

4. WEBSITE ATTRIBUTE:
   - website=True: Enables website context (theme, menu, snippets)
   - website=False: Raw HTTP response without website wrapper

5. CSRF PROTECTION:
   - type='http': CSRF token required for POST (automatic in forms)
   - type='json': CSRF token in JSON-RPC header
   - Prevents cross-site request forgery attacks

6. MODEL CONVERTERS:
   - <model("model.name"):variable> in route
   - Automatically fetches record, returns 404 if not found
   - Cleaner than manual record.browse()

CONTROLLER METHODS:
===================

This controller provides 4 main routes:

1. /events
   - Lists all published events
   - GET, auth=public, website=True
   - Accessible to everyone

2. /events/<model:event>
   - Shows single event detail
   - GET, auth=public, website=True
   - Uses model converter for clean URLs

3. /events/book
   - Submits booking form
   - POST, auth=user, website=True
   - CSRF protected, requires login

4. Sitemap
   - Generates XML sitemap for SEO
   - Lists all public event URLs
   - Helps search engines index pages
"""

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


# ========================================================================
# SITEMAP GENERATOR FUNCTION (MODULE-LEVEL)
# ========================================================================

def sitemap_events(env, rule, qs):
    """
    Generate sitemap entries for all published events.

    SITEMAP PURPOSE:
        - Helps search engines (Google, Bing) discover pages
        - Lists all public URLs with metadata (priority, frequency)
        - Automatically called by Odoo's sitemap generator

    HOW IT WORKS:
        1. Route /events has sitemap=sitemap_events parameter
        2. When generating sitemap.xml, Odoo calls this function
        3. Function yields/returns URLs to include

    PARAMETERS:
        env: Odoo environment (like request.env)
        rule: Routing rule being processed
        qs: Query string (not used here)

    YIELDS:
        Dictionaries with:
        - loc: URL path
        - priority: 0.0-1.0 (higher = more important)
        - changefreq: How often page changes

    REGISTRATION:
        This function is called because:
        1. @http.route('/events', sitemap=sitemap_events)
        2. Odoo passes this function reference to the route
        3. When building sitemap, Odoo calls it automatically
    """

    # Get all published events
    events = env['service.event'].sudo().search([
        ('state', '=', 'published'),
        ('active', '=', True),
    ])

    # Yield main events listing page
    yield {
        'loc': '/events',
        'priority': 0.8,
        'changefreq': 'daily',
    }

    # Yield individual event pages
    for event in events:
        yield {
            'loc': '/events/%s' % event.id,
            'priority': 0.6,
            'changefreq': 'weekly',
        }


class ServiceEventWebsite(http.Controller):
    """
    Website controller for Service Event pages.

    Handles public event browsing and booking submissions.
    """

    # ========================================================================
    # EVENT LISTING PAGE (GET)
    # ========================================================================

    @http.route('/events', type='http', auth='public', website=True, sitemap=sitemap_events)
    def events_list(self, **kwargs):
        """
        Display list of all published events.

        ROUTE ATTRIBUTES:
            - type='http': HTTP request (not JSON-RPC)
            - auth='public': No login required
            - website=True: Render with website theme/layout
            - sitemap=True: Include this URL in sitemap.xml

        KWARGS:
            - **kwargs: Captures URL query parameters
            - Example: /events?category=1&search=python
            - Access via kwargs.get('category'), kwargs.get('search')

        RETURNS:
            - Rendered QWeb template with event data

        SEARCH/FILTER LOGIC:
            - Only shows published events (state='published')
            - Future: Add category filter, search, pagination

        USAGE:
            GET /events → Shows all published events
            GET /events?category=1 → Filter by category (future)
        """

        # Get published events only
        events = request.env['service.event'].sudo().search([
            ('state', '=', 'published'),
            ('active', '=', True),
        ], order='start_datetime asc')

        # Get all categories for filter menu (future use)
        categories = request.env['service.event.category'].sudo().search([])

        # Prepare template values
        values = {
            'events': events,
            'categories': categories,
            'page_name': 'events',
        }

        # Render template
        return request.render('service_event_website.events_listing', values)

    # ========================================================================
    # EVENT LISTING PAGE - EXPLANATION
    # ========================================================================
    #
    # WHY sudo()?
    #     Public users don't have read access to service.event by default.
    #     sudo() bypasses access rights to show published events.
    #     SECURITY: We still filter by state='published' to avoid leaking drafts.
    #
    # WHY search() not browse()?
    #     search() finds records matching domain
    #     browse() requires known IDs
    #     We want to LIST all matching events, so search() is correct
    #
    # request.render():
    #     - Takes template XML ID
    #     - Takes dictionary of values (available in template as variables)
    #     - Returns rendered HTML response
    #
    # ALTERNATIVE PATTERNS:
    #     - Could use website.render() (same thing)
    #     - Could return request.redirect() for redirects
    #     - Could return werkzeug.wrappers.Response() for custom responses
    # ========================================================================

    # ========================================================================
    # EVENT DETAIL PAGE (GET, MODEL CONVERTER)
    # ========================================================================

    @http.route('/events/<model("service.event"):event>', type='http', auth='public', website=True, sitemap=True)
    def event_detail(self, event, **kwargs):
        """
        Display single event detail page.

        MODEL CONVERTER:
            - <model("service.event"):event> in route
            - Odoo automatically fetches the record
            - If record doesn't exist → 404 error
            - If record exists → passed as 'event' parameter

        ROUTE EXAMPLES:
            /events/1 → Fetches event with ID=1
            /events/python-workshop-25 → Uses slug if configured
            /events/999 → Returns 404 if doesn't exist

        PARAMETERS:
            event: service.event record (auto-fetched by model converter)
            **kwargs: URL query parameters (not used here)

        RETURNS:
            Rendered event detail template

        ACCESS CONTROL:
            - auth='public' allows anyone to view
            - We check event.state == 'published' to prevent draft leaks
            - Redirect to 404 if event is not published
        """

        # Security check: Only show published events
        if event.state != 'published':
            return request.redirect('/events')

        # Check if user is logged in (for booking button)
        is_logged_in = not request.env.user._is_public()

        # Get related bookings if user is logged in
        user_bookings = []
        if is_logged_in:
            user_bookings = request.env['service.booking'].search([
                ('event_id', '=', event.id),
                ('partner_id', '=', request.env.user.partner_id.id),
            ])

        # Prepare template values
        values = {
            'event': event,
            'is_logged_in': is_logged_in,
            'user_bookings': user_bookings,
            'page_name': 'event_detail',
        }

        return request.render('service_event_website.event_detail', values)

    # ========================================================================
    # MODEL CONVERTER DEEP DIVE
    # ========================================================================
    #
    # WHAT IT DOES:
    #     1. Extracts ID from URL (/events/5 → ID=5)
    #     2. Calls service.event.browse(5)
    #     3. Checks if record exists
    #     4. Passes record to method or returns 404
    #
    # BENEFITS:
    #     - Cleaner URLs (/events/5 vs /events?id=5)
    #     - Automatic 404 handling
    #     - Less boilerplate code
    #     - Type safety (always get a record)
    #
    # SLUG SUPPORT:
    #     - Can use /events/python-workshop-25 instead of /events/25
    #     - Requires website_slug field on model
    #     - Better for SEO (keywords in URL)
    #
    # ALTERNATIVE WITHOUT CONVERTER:
    #     @http.route('/events/<int:event_id>')
    #     def event_detail(self, event_id, **kwargs):
    #         event = request.env['service.event'].browse(event_id)
    #         if not event.exists():
    #             return request.not_found()
    #         # ... rest of code
    #
    # WHY _is_public()?
    #     - request.env.user always exists (public user if not logged in)
    #     - _is_public() returns True for anonymous visitors
    #     - _is_public() returns False for logged-in users
    # ========================================================================

    # ========================================================================
    # BOOKING FORM SUBMISSION (POST, CSRF PROTECTED)
    # ========================================================================

    @http.route('/events/book', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def event_book(self, **post):
        """
        Handle booking form submission.

        ROUTE ATTRIBUTES:
            - type='http': HTTP POST request
            - auth='user': Requires logged-in user (not public)
            - methods=['POST']: Only accepts POST requests
            - website=True: Maintain website context
            - csrf=True: Require CSRF token (default for POST)

        CSRF PROTECTION:
            - Prevents cross-site request forgery
            - Form must include CSRF token:
              <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
            - If token missing/invalid → 400 Bad Request error

        POST DATA:
            - **post: Dictionary of form fields
            - Example: {'event_id': '5', 'partner_id': '10', 'quantity': '2'}
            - Access via post.get('event_id')

        RETURNS:
            - Redirect to confirmation page on success
            - Re-render form with errors on failure

        ERROR HANDLING:
            - Try/except for validation errors
            - Show user-friendly error messages
            - Log errors for debugging
        """

        # Validate required fields
        event_id = post.get('event_id')
        if not event_id:
            return request.redirect('/events')

        try:
            # Get event and validate
            event = request.env['service.event'].sudo().browse(int(event_id))

            if not event.exists() or event.state != 'published':
                raise ValidationError("Event not available for booking")

            # Check capacity
            if event.capacity > 0 and event.available_seats <= 0:
                raise ValidationError("Event is fully booked")

            # Create booking
            booking = request.env['service.booking'].create({
                'event_id': event.id,
                'partner_id': request.env.user.partner_id.id,
                'booking_date': http.request.env.context.get('tz') or 'UTC',
                'state': 'draft',
            })

            # Confirm booking
            booking.action_confirm()

            # Redirect to confirmation page
            return request.redirect('/events/booking/%s/confirm' % booking.id)

        except ValidationError as e:
            # Show error message to user
            return request.render('service_event_website.booking_error', {
                'error_message': str(e),
                'event': event,
            })
        except Exception as e:
            # Log unexpected errors
            request.env['ir.logging'].sudo().create({
                'name': 'Booking Error',
                'type': 'server',
                'level': 'error',
                'message': str(e),
                'path': 'service_event_website.controllers.main',
            })

            return request.render('service_event_website.booking_error', {
                'error_message': 'An unexpected error occurred. Please try again.',
            })

    # ========================================================================
    # POST METHOD EXPLANATION
    # ========================================================================
    #
    # WHY POST not GET?
    #     - POST is for actions that change data (create booking)
    #     - GET is for retrieving data (view events)
    #     - POST requests are not cached by browsers
    #     - POST prevents accidental double-submission via browser refresh
    #
    # WHY auth='user'?
    #     - Bookings require customer information
    #     - Must be logged in to book (portal or internal user)
    #     - Public users redirected to login page
    #
    # request.env.user:
    #     - Always exists (public user if not logged in)
    #     - Has partner_id (res.partner record for user)
    #     - For public users: partner_id is "Public User" partner
    #
    # CSRF TOKEN REQUIREMENT:
    #     - All POST forms MUST include:
    #       <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
    #     - Without it: 400 Bad Request error
    #     - Protects against malicious websites submitting forms
    #
    # ERROR HANDLING PATTERN:
    #     1. Try to process booking
    #     2. Catch ValidationError (business logic errors) → Show to user
    #     3. Catch Exception (unexpected errors) → Log and show generic message
    #     4. Always provide user feedback (success or error)
    # ========================================================================

    # ========================================================================
    # BOOKING CONFIRMATION PAGE (GET)
    # ========================================================================

    @http.route('/events/booking/<int:booking_id>/confirm', type='http', auth='user', website=True)
    def booking_confirmation(self, booking_id, **kwargs):
        """
        Display booking confirmation page.

        ROUTE PATTERN:
            - <int:booking_id>: URL parameter (integer only)
            - Example: /events/booking/42/confirm → booking_id=42

        ACCESS CONTROL:
            - auth='user': Requires login
            - Check booking belongs to current user
            - Return 403 if user doesn't own the booking

        RETURNS:
            Confirmation template with booking details
        """

        # Get booking
        booking = request.env['service.booking'].browse(booking_id)

        # Security check: Only show user's own bookings
        if not booking.exists() or booking.partner_id != request.env.user.partner_id:
            return request.redirect('/events')

        values = {
            'booking': booking,
            'event': booking.event_id,
            'page_name': 'booking_confirmation',
        }

        return request.render('service_event_website.booking_confirmation', values)


# ========================================================================
# SITEMAP EXPLANATION
# ========================================================================
#
# WHAT IS SITEMAP.XML?
#     - XML file listing all public pages on website
#     - Submitted to search engines for indexing
#     - Accessible at: https://yoursite.com/sitemap.xml
#
# HOW IT WORKS IN ODOO:
#     1. Define a generator function (yields dictionaries)
#     2. Pass function to @http.route(sitemap=function_name)
#     3. When user visits /sitemap.xml, Odoo calls all sitemap functions
#     4. Results combined into one XML document
#
# PRIORITY VALUES:
#     - 1.0: Most important pages (homepage)
#     - 0.8: Important pages (main category pages)
#     - 0.6: Regular pages (individual products/events)
#     - 0.4: Less important pages (old blog posts)
#
# CHANGEFREQ VALUES:
#     - always: Page changes with every access
#     - hourly: Updated every hour
#     - daily: Updated daily
#     - weekly: Updated weekly
#     - monthly: Updated monthly
#     - yearly: Rarely updated
#     - never: Archived content
#
# SEO BENEFITS:
#     - Faster discovery of new pages
#     - Better crawling efficiency
#     - Improved search rankings
#     - Shows when pages were last modified
#
# EXAMPLE OUTPUT (sitemap.xml):
#     <?xml version="1.0" encoding="UTF-8"?>
#     <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#         <url>
#             <loc>https://example.com/events</loc>
#             <priority>0.8</priority>
#             <changefreq>daily</changefreq>
#         </url>
#         <url>
#             <loc>https://example.com/events/1</loc>
#             <priority>0.6</priority>
#             <changefreq>weekly</changefreq>
#         </url>
#     </urlset>
# ========================================================================
