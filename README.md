# Odoo-Full-Stack-Application

# Odoo Full‑Stack Practice Assignment – Specification

## 1. Objective

The goal of this assignment is to **practically cover end‑to‑end Odoo development**: backend (models, business logic, security), frontend (website & portal pages), and integration aspects (controllers, JSON routes).
This exercise is meant to strengthen understanding of **real‑world Odoo patterns**, not just isolated features.

The goal here is to explore following concepts

* Relational fields
* Computed fields(non stored with search and inverse function)
* Related Fields
* Python and SQL Constrains
* Model methods like create, read, write, unlink, search, search_count, search_fetch
* Understand concept of Recordset and Model class
* Object Relational Mapping
* Controller routing
* Controller type json/http, model converters, method get/post, CSRF tokens, CORS, website, sitemap attributes
* Tools methods(widely used)
* Understand Context and Domain
* How to create Website Page
* Snippets, snippets options and Interactions(Website Builder part)
* Security(Groups, Access Rights, Record Rules)
* API, Environment
* _inherit and _inherits
* View Inheritance
* _rec_name and display_name magical field
* What are the 5 magical fields created automatically?
* What is the role of "active" field?
* Aggregate Functions
* Type of models: BaseModel, Models, TransientModel, AbstractModel
* Autovaccum(Will be used in case of TransientModel)
*

Advance Topics
* Create Component for Backend Webclient(Field Widget)
* Create new View for Backend Webclient


## Apart from above points which we will develop in application, we also want to explore following stuff
* Asset Bundle
* What is ir.model.data?
* init, pre-init hook, post-init hook

---

## 2. Business Use Case (Suggested)

Build a **Website Event & Service Booking System**.

### High‑level idea

* Company publishes **Services / Events** on the website
* Public users can view them
* Logged‑in portal users can **submit booking/registration requests**
* Internal users manage, approve, and track requests

(You may rename models, but functional coverage must remain the same.)

---

## 3. Module Structure (Multi-module Architecture)

This assignment must be implemented using **two separate modules** to demonstrate modular design and inheritance concepts.

---

### 3.1 Base Module – Core Business Logic

Example name:

* `service_event_base`

Responsibilities:

* Core models (Event / Service, Registration / Booking)
* Business logic
* Constraints, compute methods
* Security (groups, access rights, record rules)
* Sequences
* Init / pre-init / post-init hooks

Must NOT include:

* Website pages
* Website controllers
* Snippets

---

### 3.2 Website Module – Website & Portal Integration

Example name:

* `service_event_website`

Dependencies:

* `service_event_base`
* `website`
* `portal`

Responsibilities:

* Website pages (listing, detail)
* Portal pages
* Website controllers (http / json)
* Website snippets & snippet options
* Frontend interactions (JS)

---

### 3.3 Dependency Declaration

The website module **must depend on the base module** in `__manifest__.py`.

Example:

```python
'depends': ['service_event_base', 'website', 'portal'],
```

---

## 4. Models & Business Logic

Create a **custom Odoo module** (e.g. `website_service_booking`).

Must include:

* `__manifest__.py`
* `models/`
* `controllers/`
* `security/`
* `views/`
* `data/`
* `static/`

---

## 4. Models & Business Logic

### 4.1 Core Models

#### Service / Event Model

* Fields:

  * `name` (Char, required)
  * `description` (Html)
  * `price` (Float)
  * `active` (Boolean)
  * `category_id` (Many2one)
  * `tag_ids` (Many2many)
  * `company_id` (Many2one, default current company)
  * `booking_ids` (One2many)

#### Booking / Registration Model

* Fields:

  * `name` (Char, sequence‑based)
  * `partner_id` (Many2one → res.partner)
  * `service_id` (Many2one)
  * `state` (Selection: draft / confirmed / cancelled)
  * `booking_date` (Datetime)
  * `amount` (Float – computed)
  * `company_id` (Many2one)

### 4.2 ORM Concepts (Mandatory)

#### Constraints

* Python constraint:

  * Prevent booking past dates
* SQL constraint:

  * Unique booking per partner per service

#### Compute Fields

* Stored compute:

  * `amount = service.price * quantity`

* Non‑stored compute with **search & inverse**:

  * Example: `is_expensive`

    * Computed based on amount
    * Custom `search` method
    * `inverse` method to adjust price

#### Method Overrides

* Override:

  * `create()` → auto‑generate sequence, default state
  * `write()` → restrict changes after confirmation
  * `search()` → apply default domain based on user group

Use correct decorators:

* `@api.model`
* `@api.depends`
* `@api.constrains`

## 5. Website Pages

### 5.1 Public Website Pages

* Service/Event listing page
* Service/Event detail page

Requirements:

* Use QWeb templates
* Use website controllers
* SEO‑friendly URLs
* Fetch records via controllers (not direct model calls in template)

## 6. Website Builder – Options & Interactions

### 6.0 Example: Snippet & Options (Reference Implementation)

The following example is **illustrative** and sets expectations for structure and patterns. Team members may adapt naming but must cover the same concepts.

#### A. Snippet XML (QWeb)

Example: Service Cards Snippet

Key expectations:
* Use `data-snippet` identifier
* No business logic in template
* Data provided via controller / RPC

#### B. Snippet Registration
#### C. Snippet Options XML
#### D. Snippet Options JS

Must demonstrate:

* `_rpc()` usage
* Dynamic DOM update

#### E. Controller for Snippet Reload

What evaluators should look for:

* Clean separation of concerns
* Proper editor interaction
* No direct ORM calls inside QWeb

---

### 6.1 Snippets

Create **custom website snippets** for Services / Events.

Requirements:

* Snippet to display service cards (image, name, price)
* Snippet to display featured services
* Snippet must be draggable from Website Builder

---

### 6.2 Snippet Options (Editor Sidebar)

Each snippet must expose configurable **options**:

* Select service category
* Toggle price visibility
* Limit number of records
* Sorting (price / name)

Technical expectations:

* Use `options.js`
* Extend `website.snippet.options`
* Read/write snippet dataset values
* Proper default values

---

### 6.3 Snippet Interactions

Add **interactive behaviors**:

* Dynamic reload when option changes
* AJAX/JSON call to fetch updated data
* Graceful fallback when no records found

Use:

* `this._rpc()`
* Debouncing where needed

---

### 6.4 Website Builder Integrations

Must demonstrate:

* Snippet visibility rules
* Editable vs non-editable elements
* Use of `data-oe-*` attributes
* Translatable snippet content

---

## 7. Controllers

### 6.1 HTTP Controllers

* Route to display services
* Route to submit booking form

Requirements:

* Use `type='http'`
* Handle GET & POST
* Use **CSRF token properly**
* Validate input before create

### 6.2 JSON Controllers

* Route to fetch service price dynamically
* Route to validate availability

Requirements:

* Use `type='json'`
* Return structured JSON response
* Handle access rights explicitly

---

## 7. Portal Integration

### 7.1 Portal Pages

* Portal listing of user’s bookings
* Booking detail page

Requirements:

* Extend `CustomerPortal`
* Use `portal_my_*` pattern
* Pagination support
* Access restricted to logged‑in user’s records only

---

## 8. Security

### 8.1 Groups

Create groups:

* Service User
* Service Manager

### 8.2 Access Rights

* `ir.model.access.csv`
* Users can read own bookings
* Managers can create/update all

### 8.3 Record Rules

* Portal users → only own bookings
* Multi‑company compatible rules

---

## 9. Tools & Utilities

Mandatory usage of:

* `odoo.tools` (e.g. `float_compare`, `format_date`)
* `fields.Datetime.context_timestamp`
* Sequences via `ir.sequence`
* Context usage (`self.env.context`)

---

## 10. Initialization, Hooks & Lifecycle (Mandatory)

This module must demonstrate understanding of **Odoo lifecycle hooks** and initialization patterns.

---

### 10.1 Init Function (`init.py` / model init)

Use of `init` method for:

* Creating or updating SQL objects (indexes, views)
* Data migration logic not suitable for XML

Example expectations:

* Create a PostgreSQL index for performance
* Initialize materialized view or custom SQL view

Guidelines:

* Use `self.env.cr.execute()`
* Ensure idempotency (safe to run multiple times)
* Avoid business logic in init

---

### 10.2 Pre-init Hook

Define a **pre-init hook** in `__manifest__.py`.

Purpose:

* Prepare database before module installation
* Cleanup or validate existing data

Example use cases:

* Rename old tables/columns
* Backup critical data
* Drop conflicting constraints

Requirements:

* Function placed in `hooks.py`
* Receives `cr` as argument
* Must not rely on ORM

---

### 10.3 Post-init Hook

Define a **post-init hook** in `__manifest__.py`.

Purpose:

* Populate initial data using ORM
* Configure defaults after installation

Example use cases:

* Create default service categories
* Assign access groups to users
* Generate sequences

Requirements:

* Function placed in `hooks.py`
* Uses `api.Environment`
* Safe to re-run

---

### 10.4 Manifest Declaration

Team members must explicitly declare hooks:

```python
'pre_init_hook': 'pre_init_hook',
'post_init_hook': 'post_init_hook',
```

---

What evaluators should check:

* Correct separation between pre-init and post-init logic
* No ORM usage in pre-init hook
* Idempotent and safe hook implementations

---

## 11. Additional Requirements

* Use related fields where appropriate
* Follow Odoo coding guidelines
* Proper docstrings for models & methods
* XML views must be valid & well‑structured
* No hard‑coded IDs

---

## 11. Deliverables

Each team member must submit:

* Working module
* Short README explaining:

  * Covered features
  * Assumptions made
* Screenshots of:

  * Website pages
  * Portal pages
  * Backend views

---

## 12. Evaluation Criteria

* Correct usage of ORM & API decorators
* Clean separation of concerns (model / controller / view)
* Security correctness
* Code readability & structure
* Real‑world applicability

---

## 13. Notes

This is **not a demo module**. Treat it as a **mini production‑ready feature**.

Also Explore following stuff as it is internally used
Asset Bundle
What is ir.model.data?
init, pre-init hook, post-init hook
Controller - Converters, methods, auth, CORS, website, sitemap etc.
