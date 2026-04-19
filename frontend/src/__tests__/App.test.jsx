import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';

// Mock all page components to avoid needing to mock their API calls
vi.mock('../pages/Overview', () => ({
  default: () => <h1>Overview Page</h1>,
}));
vi.mock('../pages/Leads', () => ({
  default: () => <h1>Leads Page</h1>,
}));
vi.mock('../pages/Graph', () => ({
  default: () => <h1>Graph Page</h1>,
}));
vi.mock('../pages/ABTesting', () => ({
  default: () => <h1>ABTesting Page</h1>,
}));
vi.mock('../pages/Learning', () => ({
  default: () => <h1>Learning Page</h1>,
}));
vi.mock('../pages/Pipeline', () => ({
  default: () => <h1>Pipeline Page</h1>,
}));

// Mock the api module
vi.mock('../api', () => ({
  getHealth: vi.fn(),
}));

import { getHealth } from '../api';
import App from '../App';

// Helper: render App with a specific initial URL using window.history
function renderAppAtPath(path) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

describe('App routing and layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: health check resolves
    getHealth.mockResolvedValue({ status: 'ok' });
  });

  afterEach(() => {
    // Reset to root after each test
    window.history.pushState({}, '', '/');
  });

  it('renders the Sidebar and main content area', async () => {
    await act(async () => {
      renderAppAtPath('/');
    });
    // Sidebar is an <aside> element
    expect(document.querySelector('aside.sidebar')).toBeTruthy();
    // Main content area
    expect(document.querySelector('main.main')).toBeTruthy();
  });

  it('renders Overview page at /', async () => {
    renderAppAtPath('/');
    expect(await screen.findByText('Overview Page')).toBeInTheDocument();
  });

  it('renders Leads page at /leads', async () => {
    renderAppAtPath('/leads');
    expect(await screen.findByText('Leads Page')).toBeInTheDocument();
  });

  it('renders Graph page at /graph', async () => {
    renderAppAtPath('/graph');
    expect(await screen.findByText('Graph Page')).toBeInTheDocument();
  });

  it('renders ABTesting page at /ab-testing', async () => {
    renderAppAtPath('/ab-testing');
    expect(await screen.findByText('ABTesting Page')).toBeInTheDocument();
  });

  it('renders Learning page at /learning', async () => {
    renderAppAtPath('/learning');
    expect(await screen.findByText('Learning Page')).toBeInTheDocument();
  });

  it('renders Pipeline page at /pipeline', async () => {
    renderAppAtPath('/pipeline');
    expect(await screen.findByText('Pipeline Page')).toBeInTheDocument();
  });

  it('redirects undefined routes to /', async () => {
    renderAppAtPath('/nonexistent');
    expect(await screen.findByText('Overview Page')).toBeInTheDocument();
  });

  it('shows "Backend online" when getHealth resolves', async () => {
    getHealth.mockResolvedValue({ status: 'ok' });
    renderAppAtPath('/');
    expect(await screen.findByText('Backend online')).toBeInTheDocument();
  });

  it('shows "Backend offline" when getHealth rejects', async () => {
    getHealth.mockRejectedValue(new Error('Network error'));
    renderAppAtPath('/');
    expect(await screen.findByText('Backend offline')).toBeInTheDocument();
  });

  it('calls getHealth exactly once on mount', async () => {
    renderAppAtPath('/');
    // Wait for the health check to complete
    await waitFor(() => {
      expect(getHealth).toHaveBeenCalledTimes(1);
    });
  });
});
