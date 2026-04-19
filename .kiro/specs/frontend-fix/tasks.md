# Implementation Plan: Frontend Fix

## Overview

Wire up `App.jsx` as a proper React Router v7 layout shell, build the four missing pages (`Graph.jsx`, `ABTesting.jsx`, `Learning.jsx`, `Pipeline.jsx`), update `Sidebar.jsx` to accept a `backendOnline` prop, and add a testing suite covering unit/example-based tests and property-based tests using Vitest + fast-check.

## Tasks

- [x] 1. Rewrite App.jsx as the layout shell and router
  - Replace the Vite starter template entirely with a `BrowserRouter` + layout shell
  - Import and render `Sidebar` and `<main className="main">` with `<Routes>`
  - Define routes for `/`, `/leads`, `/graph`, `/ab-testing`, `/learning`, `/pipeline`, and a `*` catch-all `<Navigate to="/" replace />`
  - Import `index.css` as the global stylesheet (remove `App.css` import)
  - Run a one-time `getHealth()` call on mount; store result as `backendOnline` boolean state and pass to `Sidebar`
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 8.1, 8.4_

- [x] 2. Update Sidebar.jsx to display backend connectivity status
  - Accept a `backendOnline: boolean | null` prop
  - Render "Backend online" with the existing `.status-dot` class when `true`
  - Render "Backend offline" with a `.status-dot-offline` variant (using `--hot` color) when `false`
  - Render "Checking…" with a neutral style when `null`
  - Add `.status-dot-offline` CSS rule to `index.css` mirroring `.status-dot` but using `--hot` for the dot color
  - _Requirements: 8.2, 8.3, 9.2_

- [x] 3. Implement Graph.jsx page
  - [x] 3.1 Create `frontend/src/pages/Graph.jsx`
    - On mount, call `getAllGraphs()` and store result in `data` state
    - Show `<Spinner />` while loading; show error banner on failure
    - Render a search input (`.search-input`) that filters company cards client-side by company name (case-insensitive)
    - Render company cards in a `.company-grid`; each card shows company name, node count, and a `.members-list` with member name, title, tier badge, and score bar
    - Clicking a card toggles an `expanded` state to show/hide full member details
    - Show `<EmptyState />` when no companies match the search query
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 3.2 Write property test for company cards rendering required fields
    - **Property 3: Company cards render all required fields**
    - **Validates: Requirements 4.3**
    - Use fast-check to generate arbitrary arrays of committee objects (company name, node_count ≥ 1, members array with name and title)
    - Assert each rendered card contains the company name, node count, and at least one member row with name and title

  - [ ]* 3.3 Write property test for graph search filtering
    - **Property 4: Graph search filters by company name**
    - **Validates: Requirements 4.4**
    - Use fast-check to generate arbitrary company lists and search strings
    - Assert only cards whose company name contains the query (case-insensitive) are visible; no non-matching card is rendered

- [x] 4. Implement ABTesting.jsx page
  - [x] 4.1 Create `frontend/src/pages/ABTesting.jsx`
    - On mount, call `getABStats()` and store result in `data` state
    - Show `<Spinner />` while loading; show error banner on failure
    - Render side-by-side `.ab-grid` variant cards (A vs B) for both email and LinkedIn channels
    - Each variant card shows sends, opens, replies, and conversion rate as `.metric-row` items
    - Visually highlight the winning variant (higher `conversion_rate`) with a winner badge or border; use `data.historical_analysis[channel].winner` field
    - Display session registry stats (total tracked sends) from `data.session_registry`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 4.2 Write property test for A/B winner indication
    - **Property 5: A/B winner indication matches conversion rates**
    - **Validates: Requirements 5.4**
    - Use fast-check to generate arbitrary `{ variant_a: { conversion_rate }, variant_b: { conversion_rate } }` objects where the two rates differ
    - Assert the variant with the higher rate has the winner indicator; the lower-performing variant does not

- [x] 5. Implement Learning.jsx page
  - [x] 5.1 Create `frontend/src/pages/Learning.jsx`
    - On mount, call `getLearningStats()` and store result in `data` state
    - Show `<Spinner />` while loading; show error banner on failure
    - Render each key in `data.weights` as a `.weight-bar-row` with label, progress bar, and numeric value
    - Render response event counts (replied, demoed, opened, bounced, unsubscribed) from `data.response_counts`
    - Provide a "Reset Weights" button (`.btn-danger`) that calls `resetLearning()` then re-fetches stats
    - Show a confirmation message after a successful reset; show error message on failure
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 6. Implement Pipeline.jsx page
  - [x] 6.1 Create `frontend/src/pages/Pipeline.jsx`
    - On mount, call `getPipeline()` and store result in `data` state
    - Show `<Spinner />` while loading; show error banner on failure
    - Render each agent from `data.agents` as an `.agent-card` with agent name, `.agent-status` badge, and key metadata fields
    - Render a data sources section listing Apollo CSV, Clay API, Apollo API, and Gemini API configuration statuses from `data.data_sources`
    - Render lead classification counts (Hot, Warm, Cold, Total) as `<StatCard>` components in a `.stat-grid`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 7. Checkpoint — verify the app renders end-to-end
  - Ensure all tests pass, ask the user if questions arise.
  - Confirm `App.jsx` no longer imports `App.css` or any Vite starter assets
  - Confirm all six routes render their respective page components without console errors

- [x] 8. Set up testing infrastructure and write unit/example-based tests
  - [x] 8.1 Install and configure Vitest, React Testing Library, and fast-check
    - Add `vitest`, `@vitest/ui`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, and `fast-check` as dev dependencies
    - Add a `vitest.config.js` (or extend `vite.config.js`) with `environment: 'jsdom'` and `setupFiles` pointing to a test setup file that imports `@testing-library/jest-dom`
    - Add a `test` script to `package.json`: `"test": "vitest --run"`
    - _Requirements: (infrastructure for all test requirements)_

  - [x] 8.2 Write unit tests for App routing and layout
    - Render `<App />` and verify the Sidebar and main content area are present
    - Navigate to each of the six routes and verify the correct page heading or landmark is rendered
    - Navigate to an undefined route (e.g., `/nonexistent`) and verify redirect to `/`
    - Mock `getHealth` to resolve → verify "Backend online" text appears in Sidebar footer
    - Mock `getHealth` to reject → verify "Backend offline" text appears in Sidebar footer
    - Verify `getHealth` is called exactly once on mount
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 8.3 Write unit tests for individual page loading and error states
    - For each of the four new pages (Graph, ABTesting, Learning, Pipeline): mock the API to return a pending promise and assert `<Spinner />` is rendered; mock the API to reject and assert an error message is displayed
    - _Requirements: 4.2, 4.7, 5.2, 5.6, 6.2, 6.7, 7.2, 7.6_

  - [ ]* 8.4 Write unit tests for Overview and Leads pages
    - Overview: mock `getLeadsStats` and `getPipeline`; assert all 8 StatCard labels are present
    - Leads: mock `getLeads`; assert all 7 column headers are present; click a row and verify `LeadDrawer` opens
    - _Requirements: 2.3, 3.4, 3.5_

  - [ ]* 8.5 Write unit tests for Learning reset flow
    - Mock `getLearningStats` and `resetLearning`; click "Reset Weights"; assert `POST /api/learn/reset` is called and a confirmation message appears
    - _Requirements: 6.5, 6.6_

  - [ ]* 8.6 Write unit tests for responsive sidebar
    - Set viewport width to 800px; assert the sidebar has `transform: translateX(-100%)`
    - _Requirements: 9.3_

- [x] 9. Write property-based tests for Leads page filtering
  - [ ]* 9.1 Write property test for filter parameters forwarded to API
    - **Property 1: Filter parameters are forwarded to the API**
    - **Validates: Requirements 3.1, 3.3**
    - Use fast-check to generate arbitrary `{ tier, search, sortBy, order, page }` combinations
    - Render the Leads page with those filter values and assert the URL called to `/api/leads` contains matching query parameters

  - [ ]* 9.2 Write property test for displayed leads satisfying tier filter
    - **Property 2: Displayed leads satisfy the active tier filter**
    - **Validates: Requirements 3.2**
    - Use fast-check to generate an arbitrary tier value and an arbitrary array of leads with random tiers
    - Render the Leads page with a mocked API returning those leads and the active tier filter set
    - Assert every rendered row's tier badge matches the active filter

- [x] 10. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- The design document uses React/JSX throughout — no language selection needed
- Property tests use fast-check with a minimum of 100 iterations per property
- Unit tests use Vitest + React Testing Library + jsdom
- No new runtime dependencies are required; only dev dependencies for testing
