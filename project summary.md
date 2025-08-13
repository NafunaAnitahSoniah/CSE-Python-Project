# Project Summary — XChicks

Last updated: 2025-08-13

## Overview

XChicks is a role-based Django web app for managing poultry chick requests, feed allocations, stock, deliveries, and reporting.

Primary roles:

- Manager: oversees approvals, stock, deliveries, sales, and reports.
- Sales Agent: registers farmers, submits chick requests and feed allocations, tracks their pipeline.
- Farmer: represented in the system as a Customer profile (not an app user-facing role in UI).

Core domains:

- Users and Farmers (UserProfile, Customer)
- Chick stock (ChickStock)
- Feed stock (FeedStock)
- Chick requests (ChickRequest)
- Feed allocations/requests (FeedAllocation)

Key pages: dashboards, stock management, requests/allocations lists, deliveries, sales summary, and a rich reports module with CSV/XLSX/PDF/TXT exports.

## Roles & Permissions

- All protected pages require login.
- Role routing on login:
  - Manager → `managersdashboard/`
  - Sales Agent → `salesagentdashboard/`
- Role guards:
  - Manager-only: approvals, stocks, deliveries, reports, sales, TXT exports.
  - Sales Agent-only: register farmer, add chick request, add feed request, view own requests.

## Data Model (essentials)

- UserProfile (extends Django AbstractUser)

  - Fields: role [farmer|sales_agent|manager], phone (unique, validated), title
  - Table: `farmer_users`

- Customer (Farmer)

  - One-to-one to `UserProfile`
  - `farmer_id` auto: `FARMER-YYYY-####`
  - Age auto-calculated from `date_of_birth`
  - NIN 14 alphanumeric, unique

- ChickStock

  - Batch with type [layer|broiler], breed [local|exotic]
  - Price per chick, stock quantity, updated_at (auto)
  - Guard: quantity cannot be negative

- FeedStock

  - Feed name/type/brand, quantity, prices, supplier info
  - Guard: expiry date cannot be in the past; supplier_contact unique

- ChickRequest

  - Links to Customer and created_by (sales agent)
  - Auto ID: `REQ-YYYY-####`
  - Status: pending|approved|rejected|completed (UI mainly uses pending/approved/rejected)
  - Business rules on clean():
    - Returning farmer cannot request > 500 chicks
    - Must have enough total stock across matching type+breed
    - One request per farmer every 4 months
  - Delivered flag tracked separately from status

- FeedAllocation
  - Links to FeedStock (optional) and ChickRequest (required)
  - Auto ID: `FEED-YYYY-####`
  - Default payment_due_date = 60 days from creation
  - Status: pending|approved|rejected; Payment status: pending|paid|rejected
  - Delivered flag tracked separately

## Core Features by Area

- Authentication & Routing

  - Signup creates `UserProfile` with role
  - Login redirects by role

- Sales Agent

  - Register Farmer: creates user (role=farmer) + customer profile; `farmer_id` auto
  - Add Chick Request: validates stock/limits; generates request ID
  - Add Feed Request: ties to existing chick request; picks a feed stock; generates feed ID
  - My Dash: counts by status, requested totals, delivered counts
  - Lists: my chick requests, my feed requests

- Manager
  - Dashboard: users, stock totals, request status mix (chicks+feeds), total sales (chicks+feeds), deliveries, payment stats
  - Stock management: view/update both Chick and Feed stock
  - Requests lists: chick requests, feed allocations
  - Approvals:
    - Chick request approval: checks aggregated stock by type/breed and deducts proportionally across batches; sets approved_on
    - Feed request approval: ensures linked stock has enough bags; deducts quantity
  - Deliveries: view approved items; mark delivered (chicks/feeds)
  - Sales: unified view of approved sales (feeds via bags*unit price; chicks via qty*latest price for type/breed)
  - Reports: powerful filtered reporting and multi-format export
  - TXT Exports: quick plaintext dumps for several datasets

## End-to-End Workflows

1. Farmer Onboarding

- Sales Agent fills farmer form → system creates `UserProfile(role=farmer)` and `Customer` with auto `farmer_id`.
- Age computed from DOB; NIN validated.

2. Chick Request Pipeline

- Sales Agent: selects farmer + enters details → system validates:
  - 4-month cooldown per farmer
  - Returning farmer max 500 chicks
  - Available stock across matching type/breed is sufficient
- On save: request gets `REQ-YYYY-####`, status=pending.
- Manager: reviews list, approves or rejects.
  - Approve: locks and deducts stock across multiple batches, records `approved_on`, sets status=approved.
- Delivery: Manager can mark delivered; delivery status tracked separately from approval state.

3. Feed Allocation Pipeline

- Sales Agent: picks an approved/pending chick request and a feed stock with quantity.
- On save: feed allocation gets `FEED-YYYY-####`, status=pending, payment status as provided.
- Manager: approves or rejects.
  - Approve: validates and deducts feed stock; sets status=approved.
- Delivery: Manager can mark delivered.

4. Sales & Reporting

- Sales page: summarizes monetary totals from all approved items:
  - Feed: bags_allocated × feed_stock.selling_price
  - Chicks: quantity × latest `chick_price` for the request’s type/breed
- Reports: filter across date ranges, types, statuses, agents, farmers, and text query; see stock levels, requests, allocations, agents’ contributions, trends, daily activity, weekly summaries; export to CSV/XLSX/PDF; TXT endpoints for plaintext exports.

## Reports Module (Details)

Filters: start/end date, chick_type, chick_breed, feed_type, status, agent, farmer, q (text).

Provided datasets in-page:

- Chick and Feed stock (with totals)
- Chick requests and Feed allocations (first 1000 shown)
- Stats: pending/approved/rejected mixes, pending payments, low stock count
- Charts: daily activity buckets (chicks vs feeds), status mix, weekly summaries
- Agent performance: totals/approved/rejected/delivered by agent username
- Trends: 30-day comparisons (when no date filter)

Exports:

- `reports/export?dataset=<...>&format=csv|xlsx|pdf` with datasets:
  - chick_stock, feed_stock, chick_requests, feed_allocations, farmers,
  - agent_performance, activity_daily, activity_weekly,
  - general (multi-sheet XLSX or multi-section PDF)
- TXT endpoints (plaintext): sales, chick-requests, feed-allocations, chick-stock, feed-stock, farmers

Dependencies used for exports:

- `openpyxl` (XLSX), `reportlab` (PDF). CSV/TXT require no extras.

## Business Rules & Validations

- UserProfile.phone unique; phone/NIN format validations
- Customer.age derived from DOB (synced on save/clean)
- ChickStock: quantity non-negative
- FeedStock: expiry_date not in the past
- ChickRequest:
  - Returning farmers: max 500 chicks
  - One request per farmer every 120 days
  - Sufficient aggregate stock required for type+breed
- FeedAllocation: payment_due_date defaults to +60 days

## Pricing & Inventory Notes

- Chicks revenue uses latest `chick_price` from any stock matching request type/breed at time of reporting; per-batch price distinctions aren’t preserved on the request.
- Inventory deductions:
  - Chicks: approval deducts across batches in order of highest quantity first.
  - Feed: approval deducts from the linked `FeedStock`.
- Delivered flags are independent; approval status is not auto-changed on delivery.

## Key URLs (selection)

- Public: `/`, `/signup/`, `/login/`, `/logout/`
- Manager: `/managersdashboard/`, `/chickrequests/`, `/feedrequests/`, `/deliveries/`, `/sales/`, `/reports/`, stock update pages
- Sales Agent: `/salesagentdashboard/`, `/registerfarmer/`, `/addchickrequest/`, `/addfeedrequest/`, own requests lists
- Actions:
  - Approve Chick: `/approvechickrequest/<id>/`
  - Approve Feed: `/approvefeedrequest/<id>/`
  - Mark delivered: `/deliveries/mark/chick/<id>/`, `/deliveries/mark/feed/<id>/`
  - Reports export: `/reports/export?dataset=...&format=csv|xlsx|pdf`
  - TXT exports under `/export/.../`

## Templates (high-level)

- Base layouts: `base_manager.html`, `base_agent.html`
- Auth: `signup.html`, `login.html`
- Dashboards: `managersdashboard.html`, `1salesAgentdashboard.html`
- Stocks: `chickStock.html`, `feedStock.html`, `updateChickStock.html`, `updateFeedStock.html`
- Requests: `viewChickrequests.html`, `viewFeedAllocations.html`, `1viewchickrequests.html`, `1viewfeedrequests.html`, approvals
- Sales & Reports: `sales.html`, `reports.html`
- Deliveries: `deliveries.html`
- Farmer: `1registerfarmer.html`, `farmerRecords.html`, `farmerReview.html`

## Setup & Runtime (essentials)

- Django 5.2.x, Python 3.12 (venv present: `djenv/`)
- Installed apps: `ChicksApp`, `widget_tweaks`
- Custom user model: `ChicksApp.UserProfile` (AUTH_USER_MODEL)
- DB: SQLite (`db.sqlite3`)
- Static: `STATIC_URL=/static/`, project-level `static/` directory included

Optional packages for exports:

- `openpyxl` (Excel)
- `reportlab` (PDF)

## Security & Access

- `login_required` + role checks via `role_required` decorator
- CSRF middleware enabled globally
- Password validators enabled; default DEBUG=True (dev only)

## Known Gaps / Observations

- ChickRequest status includes `completed` but flows don’t set it; delivery tracked via a separate boolean.
- Duplicate `Login`/`Logout` URL names and duplicate `Logout` view definition; harmless but redundant.
- FeedAllocation creation assumes a `feed_stock` is chosen; code will error if omitted (guarded in try/except with message).
- Pricing for chicks depends on latest stock price at report time, not price at approval time; consider persisting price on request for auditability.
- No explicit payment recording flows beyond `payment_status`; amounts due entered but not reconciled.
- `ApproveFeedRequest` sets status approved but doesn’t touch `payment_status` (except when rejecting).
- DeleteRequest template route exists but no deletion logic implemented.

## Recommended Next Steps

- Normalize pricing at transaction time: store unit price on approved requests/allocations.
- Add a “complete/closed” lifecycle state once delivered and/or paid.
- Add validations/UI for mandatory feed_stock selection; compute `amount_due` server-side.
- Introduce basic payments module or at least consistent payment status transitions.
- Resolve duplicate URLs and redundant views; add tests for role access.
- Improve reporting filters to include location on-page; align "general" export with on-page filters consistently.
- Add pagination to list views; protect heavy pages with reasonable limits.
- Add audit logs for approvals/stock movements.

## File Pointers

- Models: `XChicks/ChicksApp/models.py`
- Views: `XChicks/ChicksApp/views.py`
- URLs: `XChicks/XChicks/urls.py`
- Settings: `XChicks/XChicks/settings.py`
- Templates: `XChicks/ChicksApp/templates/`
- Static: `static/` (project), plus app static folders

---
