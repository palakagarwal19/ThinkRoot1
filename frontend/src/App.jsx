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
import './index.css';

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
