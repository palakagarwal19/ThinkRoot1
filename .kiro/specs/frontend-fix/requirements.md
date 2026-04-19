# Requirements Document

## Introduction

The NeuroLead frontend is a React/Vite single-page application that serves as the UI for a multi-agent AI lead intelligence system (P95.ai). The current codebase has all the core components and pages built (Overview, Leads, Sidebar, LeadDrawer, UI primitives), but `App.jsx` is still the default Vite starter template — meaning the actual application never renders. Additionally, four pages referenced in the Sidebar navigation (Graph, A/B Testing, Learning, Pipeline) do not yet exist.

This feature covers: wiring up the router and layout shell, building the four missing pages, and improving the overall layout and UX to a production-quality standard.

## Glossary

- **App**: The root React component (`App.jsx`) that provides the router and layout shell
- **Dashboard**: The full NeuroLead web application rendered in the browser
- **Sidebar**: The fixed left-navigation component (`Sidebar.jsx`)
- **Router**: React Router v7 instance managing client-side navigation
- **Overview Page**: The `/` route showing KPI stats and charts
- **Leads Page**: The `/leads` route showing the paginated, filterable lead table
- **Graph Page**: The `/graph` route showing buying committee graphs per company
- **AB_Testing_Page**: The `/ab-testing` route showing A/B variant performance stats
- **Learning_Page**: The `/learning` route showing response learning agent weights and stats
- **Pipeline_Page**: The `/pipeline` route showing agent statuses and data source health
- **LeadDrawer**: The slide-in panel showing full lead detail, ML score, signals, and outreach
- **API**: The FastAPI backend at `http://localhost:4000`
- **Backend_Status**: Whether the API is reachable, shown in the Sidebar footer

## Requirements

### Requirement 1: Application Routing and Layout Shell

**User Story:** As a user, I want to navigate between all sections of the NeuroLead dashboard, so that I can access lead intelligence, graphs, A/B testing, learning stats, and pipeline status from a single application.

#### Acceptance Criteria

1. THE App SHALL render a persistent layout consisting of the Sidebar and a main content area for all routes.
2. THE Router SHALL define routes for `/`, `/leads`, `/graph`, `/ab-testing`, `/learning`, and `/pipeline`.
3. WHEN a user navigates to an undefined route, THE Router SHALL redirect to the Overview Page at `/`.
4. THE Sidebar SHALL highlight the active route using the existing `active` CSS class via React Router's `NavLink`.
5. THE App SHALL import and apply `index.css` as the global stylesheet so all CSS custom properties and component styles are available across all pages.
6. THE App SHALL NOT render any default Vite starter content (counter, hero image, React/Vite logos).

---

### Requirement 2: Overview Page

**User Story:** As a sales operator, I want to see a real-time dashboard of lead KPIs and charts, so that I can quickly assess pipeline health.

#### Acceptance Criteria

1. WHEN the Overview Page mounts, THE Overview_Page SHALL fetch stats from `/api/leads/stats` and pipeline data from `/api/pipeline` in parallel.
2. WHILE data is loading, THE Overview_Page SHALL display the Spinner component.
3. THE Overview_Page SHALL display eight StatCards: Total Leads, Hot Leads, Warm Leads, Cold Leads, Avg ML Score, Emails Sent, Replies, and Demos.
4. THE Overview_Page SHALL display four charts: Lead Tier Distribution (donut), Top Industries (horizontal bar), Top Countries (pie), and Engagement Funnel (vertical bar).
5. WHEN `stats.effective_weights` is present, THE Overview_Page SHALL render a weight bar section showing each scoring weight as a labeled progress bar.
6. IF the API returns an error, THEN THE Overview_Page SHALL display an error message instead of crashing.

---

### Requirement 3: Leads Page

**User Story:** As a sales operator, I want to browse, search, filter, and sort all leads with their ML scores, so that I can prioritize outreach efficiently.

#### Acceptance Criteria

1. WHEN the Leads Page mounts, THE Leads_Page SHALL fetch leads from `/api/leads` with the current filter, sort, and pagination parameters.
2. THE Leads_Page SHALL support filtering by tier (Hot / Warm / Cold / All), free-text search across name, company, and email, and sorting by score, company, or country.
3. WHEN a filter or sort parameter changes, THE Leads_Page SHALL reset to page 1 and re-fetch.
4. THE Leads_Page SHALL display leads in a table with columns: Name/Company, Title, Industry, Country, Tier badge, Score bar, and external links (LinkedIn, Website).
5. WHEN a user clicks a table row, THE Leads_Page SHALL open the LeadDrawer for that lead's ID.
6. THE Leads_Page SHALL render pagination controls showing the current page, total pages, and total lead count.
7. IF no leads match the active filters, THEN THE Leads_Page SHALL display the EmptyState component with an appropriate message.

---

### Requirement 4: Graph Page

**User Story:** As a sales operator, I want to view buying committee graphs per company, so that I can identify all stakeholders at a target account.

#### Acceptance Criteria

1. WHEN the Graph Page mounts, THE Graph_Page SHALL fetch all company graphs from `/api/graph`.
2. WHILE data is loading, THE Graph_Page SHALL display the Spinner component.
3. THE Graph_Page SHALL display each company as a card showing the company name, node count, and a list of committee members with their name, title, and ML score.
4. THE Graph_Page SHALL display a search input that filters the visible company cards by company name in real time (client-side).
5. WHEN a company card is clicked, THE Graph_Page SHALL expand or highlight the card to show full member details including tier badges and score bars.
6. IF no companies match the search query, THEN THE Graph_Page SHALL display the EmptyState component.
7. IF the API returns an error, THEN THE Graph_Page SHALL display an error message.

---

### Requirement 5: A/B Testing Page

**User Story:** As a sales operator, I want to compare the performance of email and LinkedIn outreach variants, so that I can identify which messaging drives better engagement.

#### Acceptance Criteria

1. WHEN the AB_Testing_Page mounts, THE AB_Testing_Page SHALL fetch A/B stats from `/api/ab-testing`.
2. WHILE data is loading, THE AB_Testing_Page SHALL display the Spinner component.
3. THE AB_Testing_Page SHALL display side-by-side variant cards (A vs B) for both email and LinkedIn channels, each showing sends, opens, replies, and conversion rate.
4. THE AB_Testing_Page SHALL visually indicate the winning variant (higher conversion rate) using a distinct highlight or badge.
5. THE AB_Testing_Page SHALL display session registry stats (total tracked sends) from the API response.
6. IF the API returns an error, THEN THE AB_Testing_Page SHALL display an error message.

---

### Requirement 6: Learning Page

**User Story:** As a sales operator, I want to monitor and reset the response learning agent's scoring weights, so that I can understand how the model adapts to engagement signals.

#### Acceptance Criteria

1. WHEN the Learning_Page mounts, THE Learning_Page SHALL fetch learning stats from `/api/learn/stats`.
2. WHILE data is loading, THE Learning_Page SHALL display the Spinner component.
3. THE Learning_Page SHALL display each scoring weight as a labeled progress bar showing the current adjusted value.
4. THE Learning_Page SHALL display response event counts (replied, demoed, opened, bounced, unsubscribed).
5. THE Learning_Page SHALL provide a "Reset Weights" button that calls `POST /api/learn/reset` and refreshes the displayed stats.
6. WHEN the reset succeeds, THE Learning_Page SHALL display a confirmation message.
7. IF the API returns an error, THEN THE Learning_Page SHALL display an error message.

---

### Requirement 7: Pipeline Page

**User Story:** As a developer or operator, I want to see the health and configuration of all backend agents and data sources, so that I can verify the system is running correctly.

#### Acceptance Criteria

1. WHEN the Pipeline_Page mounts, THE Pipeline_Page SHALL fetch pipeline status from `/api/pipeline`.
2. WHILE data is loading, THE Pipeline_Page SHALL display the Spinner component.
3. THE Pipeline_Page SHALL display each agent as a card showing the agent name, status badge, and key metadata (source, model, library, etc.).
4. THE Pipeline_Page SHALL display a data sources section showing the configuration status of Apollo CSV, Clay API, Apollo API, and Gemini API.
5. THE Pipeline_Page SHALL display lead classification counts (Hot, Warm, Cold, Total) as StatCards.
6. IF the API returns an error, THEN THE Pipeline_Page SHALL display an error message.

---

### Requirement 8: Backend Connectivity Status

**User Story:** As a user, I want to see whether the backend is reachable, so that I know if the data I'm viewing is live.

#### Acceptance Criteria

1. WHEN the Dashboard loads, THE Dashboard SHALL call `GET /` to check backend health.
2. WHEN the health check succeeds, THE Sidebar SHALL display "Backend online" with a green animated pulse indicator.
3. WHEN the health check fails, THE Sidebar SHALL display "Backend offline" with a red indicator.
4. THE Backend_Status check SHALL run once on application mount and SHALL NOT poll continuously.

---

### Requirement 9: Layout and Visual Quality

**User Story:** As a user, I want a polished, consistent layout across all pages, so that the application feels professional and is easy to use.

#### Acceptance Criteria

1. THE Dashboard SHALL use a fixed-width sidebar (240px) with the main content area occupying the remaining viewport width.
2. THE Dashboard SHALL apply the dark color scheme defined in `index.css` (CSS custom properties: `--bg-base`, `--bg-surface`, `--bg-card`, etc.) consistently across all pages.
3. WHEN the viewport width is below 900px, THE Sidebar SHALL be hidden off-screen and THE main content area SHALL occupy the full viewport width.
4. THE Dashboard SHALL use the `slide-up` animation class on each page's root element for smooth page transitions.
5. THE Dashboard SHALL render all interactive elements (buttons, inputs, selects) using the existing CSS classes (`btn`, `btn-primary`, `btn-ghost`, `filter-select`, `search-input`) for visual consistency.
6. THE Dashboard SHALL use `Space Grotesk` for headings and `Inter` for body text as defined in `index.css`.
