# Design Document: Frontend Fix

## Overview

The NeuroLead frontend is a React 19 / Vite 8 single-page application. All the core building blocks already exist — `Sidebar.jsx`, `LeadDrawer.jsx`, `UI.jsx`, `Overview.jsx`, and `Leads.jsx` — but `App.jsx` is still the default Vite starter template, so the application never renders. Four pages referenced in the sidebar navigation (Graph, A/B Testing, Learning, Pipeline) are also missing.

This design covers three areas of work:

1. **App shell wiring** — replace `App.jsx` with a proper React Router v7 layout shell that mounts the Sidebar and routes to all pages.
2. **Four missing pages** — implement `Graph.jsx`, `ABTesting.jsx`, `Learning.jsx`, and `Pipeline.jsx` using the existing API client (`api.js`) and CSS design system (`index.css`).
3. **Backend health indicator** — add a one-time health check on mount that updates the Sidebar footer status.

No new dependencies are required. The project already has `react-router-dom@7`, `recharts@3`, and `lucide-react`.

---

## Architecture

The application follows a flat, single-level component hierarchy with a shared layout shell:

```
main.jsx
└── App.jsx  (BrowserRouter + layout shell)
    ├── Sidebar.jsx  (fixed left nav, health status)
    └── <main class="main">
        └── <Routes>
            ├── /              → Overview.jsx   (already exists)
            ├── /leads         → Leads.jsx      (already exists)
            ├── /graph         → Graph.jsx      (new)
            ├── /ab-testing    → ABTesting.jsx  (new)
            ├── /learning      → Learning.jsx   (new)
            ├── /pipeline      → Pipeline.jsx   (new)
            └── *              → <Navigate to="/" />
```

State is local to each page component. There is no global state manager — each page fetches its own data on mount. The only cross-cutting concern is the backend health status, which is fetched once in `App.jsx` and passed as a prop to `Sidebar`.

### Data Flow

```
App.jsx
  │  mount → GET /  (health check, once)
  │  passes { backendOnline: bool } → Sidebar
  │
  └── Route renders page component
        │  mount → GET /api/<endpoint>
        │  loading state → <Spinner />
        │  success → render data
        └── error state → error message
```

---

## Components and Interfaces

### App.jsx (rewrite)

Replaces the Vite starter template entirely.

```jsx
// Responsibilities:
// 1. Wrap everything in <BrowserRouter>
// 2. Run one-time health check on mount
// 3. Render layout: <Sidebar backendOnline={bool} /> + <main> with <Routes>
// 4. Define all six routes + catch-all redirect

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import Leads from './pages/Leads';
import Graph from './pages/Graph';
import ABTesting from './pages/ABTesting';
import Learning from './pages/Learning';
import Pipeline from './pages/Pipeline';
import { getHealth } from './api';

export default function App() {
  const [backendOnline, setBackendOnline] = useState(null); // null = checking

  useEffect(() => {
    getHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []); // empty deps = run once on mount

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar backendOnline={backendOnline} />
        <main className="main">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/leads" element={<Leads />} />
            <Route path="/graph" element={<Graph />} />
            <Route path="/ab-testing" element={<ABTesting />} />
            <Route path="/learning" element={<Learning />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

### Sidebar.jsx (minor update)

Accepts a `backendOnline` prop and renders the appropriate status text and indicator color in the footer. The existing `status-dot` CSS class already provides the green pulse animation; a new `status-dot-offline` variant will use `--hot` (red) instead.

```jsx
// Props: { backendOnline: boolean | null }
// null → "Checking…" (neutral)
// true → "Backend online" (green pulse, existing .status-dot)
// false → "Backend offline" (red, .status-dot-offline)
```

### Graph.jsx (new page)

```
State:
  data: { total_companies, committees: [...] } | null
  loading: boolean
  error: string | null
  search: string
  expanded: string | null  (company name of expanded card)

On mount: getAllGraphs() → GET /api/graph
Client-side filter: committees filtered by search against company name
```

Each committee object from the API has shape:
```json
{
  "company": "Acme Corp",
  "node_count": 4,
  "members": [
    { "id": "...", "name": "Jane Doe", "title": "CTO", "score": 82, "tier": "Hot" }
  ]
}
```

### ABTesting.jsx (new page)

```
State:
  data: { historical_analysis, session_registry } | null
  loading: boolean
  error: string | null

On mount: getABStats() → GET /api/ab-testing
```

`historical_analysis` shape (from `ab_agent.py`):
```json
{
  "email": {
    "variant_a": { "sends": 10, "opens": 4, "replies": 2, "conversion_rate": 0.2 },
    "variant_b": { "sends": 10, "opens": 6, "replies": 3, "conversion_rate": 0.3 },
    "winner": "B"
  },
  "linkedin": { ... }
}
```

### Learning.jsx (new page)

```
State:
  data: { weights, response_counts, total_responses } | null
  loading: boolean
  error: string | null
  resetting: boolean
  resetMsg: string | null

On mount: getLearningStats() → GET /api/learn/stats
Reset button: resetLearning() → POST /api/learn/reset → re-fetch stats
```

`weights` is an object like `{ icp_match: 0.35, seniority: 0.25, ... }`.

### Learning.jsx (new page)

```
State:
  data: { weights, response_counts, total_responses } | null
  loading: boolean
  error: string | null
  resetting: boolean
  resetMsg: string | null

On mount: getLearningStats() → GET /api/learn/stats
Reset button: resetLearning() → POST /api/learn/reset → re-fetch stats
```

### Pipeline.jsx (new page)

```
State:
  data: { pipeline, agents, lead_classification, data_sources } | null
  loading: boolean
  error: string | null

On mount: getPipeline() → GET /api/pipeline
```

`agents` is an object keyed by agent name, each with `status` and metadata fields.
`lead_classification` has `{ hot, warm, cold, total }`.
`data_sources` has `{ primary, clay_api, apollo_api, gemini_api, ... }`.

---

## Data Models

### Route → Page → API mapping

| Route | Component | API Endpoint | Key Response Fields |
|---|---|---|---|
| `/` | Overview | `GET /api/leads/stats`, `GET /api/pipeline` | `tier_counts`, `top_industries`, `engagement`, `effective_weights` |
| `/leads` | Leads | `GET /api/leads` | `leads[]`, `total`, `total_pages` |
| `/graph` | Graph | `GET /api/graph` | `committees[]`, `total_companies` |
| `/ab-testing` | ABTesting | `GET /api/ab-testing` | `historical_analysis`, `session_registry` |
| `/learning` | Learning | `GET /api/learn/stats` | `weights`, `response_counts`, `total_responses` |
| `/pipeline` | Pipeline | `GET /api/pipeline` | `agents{}`, `lead_classification`, `data_sources` |

### Lead (list view, from `/api/leads`)

```typescript
interface LeadSlim {
  id: string;
  name: string;
  title: string | null;
  company: string | null;
  email: string | null;
  industry: string | null;
  country: string | null;
  linkedin_url: string | null;
  website: string | null;
  ml_score: {
    score: number;       // 0–100
    tier: 'Hot' | 'Warm' | 'Cold';
    components: Record<string, number>;
  };
}
```

### Committee (from `/api/graph`)

```typescript
interface Committee {
  company: string;
  node_count: number;
  members: Array<{
    id: string;
    name: string;
    title: string;
    score: number;
    tier: string;
  }>;
}
```

### ABStats (from `/api/ab-testing`)

```typescript
interface VariantStats {
  sends: number;
  opens: number;
  replies: number;
  conversion_rate: number;
}
interface ChannelStats {
  variant_a: VariantStats;
  variant_b: VariantStats;
  winner: 'A' | 'B' | 'tie' | null;
}
interface ABData {
  historical_analysis: { email: ChannelStats; linkedin: ChannelStats };
  session_registry: { total_tracked: number; [key: string]: unknown };
}
```

### LearningStats (from `/api/learn/stats`)

```typescript
interface LearningStats {
  weights: Record<string, number>;
  response_counts: Record<string, number>;
  total_responses: number;
}
```

### PipelineData (from `/api/pipeline`)

```typescript
interface PipelineData {
  pipeline: string;
  agents: Record<string, { status: string; [key: string]: unknown }>;
  lead_classification: { hot: number; warm: number; cold: number; total: number };
  data_sources: Record<string, string>;
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

This feature is primarily a UI wiring and page-building task. Most acceptance criteria are specific examples (does this element render?) or edge cases (does the error state show?). However, several criteria involve universal behavior across varying inputs — filtering, rendering collections, and winner determination — which are suitable for property-based testing.

The property-based testing library chosen is **fast-check** (JavaScript/TypeScript), which integrates well with Vitest.

### Property Reflection

Before writing properties, reviewing for redundancy:

- **3.1 (API params)** and **3.2 (filter display)** both relate to filtering but test different layers — the query string sent vs. the items displayed. They are complementary, not redundant.
- **4.3 (company card rendering)** and **4.4 (search filtering)** test different behaviors on the same data — rendering completeness vs. filter correctness. Not redundant.
- **6.3 (weight bars)** and **7.3 (agent cards)** both test "for any collection, each item is rendered with required fields." They are the same pattern applied to different data shapes — kept as separate properties since the data models differ.
- **5.4 (winner indication)** is unique — no other property covers it.

After reflection: 5 distinct properties, no redundancy.

---

### Property 1: Filter parameters are forwarded to the API

*For any* combination of tier filter, search string, sort field, sort order, and page number, when the Leads page fetches data, the HTTP request to `/api/leads` SHALL include query parameters that exactly match the active filter state.

**Validates: Requirements 3.1, 3.3**

---

### Property 2: Displayed leads satisfy the active tier filter

*For any* tier filter value (Hot, Warm, Cold) and any API response, all leads rendered in the table SHALL have an `ml_score.tier` value that matches the active filter. When no filter is active, leads of any tier may appear.

**Validates: Requirements 3.2**

---

### Property 3: Company cards render all required fields

*For any* list of committee objects returned by `/api/graph`, each company card rendered by the Graph page SHALL display the company name, node count, and at least one member row containing a name and title.

**Validates: Requirements 4.3**

---

### Property 4: Graph search filters by company name

*For any* search query string and any list of companies, the Graph page SHALL display only company cards whose name contains the search query (case-insensitive), and SHALL display no cards whose name does not contain the query.

**Validates: Requirements 4.4**

---

### Property 5: A/B winner indication matches conversion rates

*For any* A/B stats object where variant A and variant B have different conversion rates, the AB Testing page SHALL visually mark the variant with the higher conversion rate as the winner, and SHALL NOT mark the lower-performing variant as the winner.

**Validates: Requirements 5.4**

---

## Error Handling

All page components follow the same error handling pattern:

1. Initialize `error` state as `null`.
2. Wrap API calls in `try/catch`.
3. On catch, set `error` to `e.message`.
4. Render an error banner (red text on `--hot-bg` background) when `error` is non-null.
5. Never let an unhandled promise rejection crash the component tree.

The `App.jsx` health check uses the same pattern but maps the result to a boolean (`backendOnline`) rather than displaying an error — the Sidebar footer communicates the status visually.

**No global error boundary is added** — each page handles its own errors independently, which is sufficient for this application's scope.

---

## Testing Strategy

### Unit / Example-Based Tests (Vitest + React Testing Library)

These cover the specific, concrete acceptance criteria:

- **App routing**: render App, navigate to each route, verify correct page component mounts; verify `*` redirects to `/`.
- **Sidebar active state**: navigate to each route, verify the corresponding `nav-link` has the `active` class.
- **Loading states**: mock fetch with a pending promise, verify `<Spinner />` is rendered for each page.
- **Error states**: mock fetch to reject, verify error message is displayed for each page.
- **Overview StatCards**: render with mocked stats, verify all 8 card labels are present.
- **Leads table columns**: render with mocked leads, verify all 7 column headers are present.
- **LeadDrawer open**: click a table row, verify drawer opens with the correct lead ID.
- **Learning reset**: click "Reset Weights", verify `POST /api/learn/reset` is called and confirmation message appears.
- **Backend health**: mount App, verify `GET /` is called exactly once; mock success → "Backend online"; mock failure → "Backend offline".
- **Responsive sidebar**: set viewport to 800px, verify sidebar has `transform: translateX(-100%)`.

### Property-Based Tests (Vitest + fast-check)

Each property test runs a minimum of 100 iterations.

**Property 1 — Filter params forwarded to API**
- Generator: arbitrary `{ tier, search, sortBy, order, page }` combinations
- Action: render Leads page with those filter values
- Assert: the URL called contains matching query params
- Tag: `Feature: frontend-fix, Property 1: filter parameters are forwarded to the API`

**Property 2 — Displayed leads satisfy tier filter**
- Generator: arbitrary tier value + arbitrary array of leads with random tiers
- Action: render Leads page with mocked API returning those leads, active tier filter set
- Assert: every rendered row's tier badge matches the filter
- Tag: `Feature: frontend-fix, Property 2: displayed leads satisfy the active tier filter`

**Property 3 — Company cards render required fields**
- Generator: arbitrary array of committee objects (company name, node_count ≥ 1, members array)
- Action: render Graph page with mocked API returning those committees
- Assert: for each committee, a card exists containing the company name, node count, and member names
- Tag: `Feature: frontend-fix, Property 3: company cards render all required fields`

**Property 4 — Graph search filters by company name**
- Generator: arbitrary list of companies + arbitrary search string
- Action: render Graph page, type search string into search input
- Assert: visible cards ⊆ companies whose name contains the query; no non-matching card is visible
- Tag: `Feature: frontend-fix, Property 4: graph search filters by company name`

**Property 5 — A/B winner matches conversion rates**
- Generator: arbitrary `{ variant_a: { conversion_rate }, variant_b: { conversion_rate } }` where rates differ
- Action: render ABTesting page with mocked data
- Assert: the variant with the higher rate has the winner indicator; the other does not
- Tag: `Feature: frontend-fix, Property 5: A/B winner indication matches conversion rates`

### Integration Tests

Not applicable for this feature — all API interactions are tested via mocks in unit/property tests. The backend already has its own test coverage.
