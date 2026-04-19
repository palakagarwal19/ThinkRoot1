import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, Brain, GitFork,
  FlaskConical, TrendingUp, Cpu, Zap
} from 'lucide-react';

const NAV = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Leads', to: '/leads', icon: Users },
  { label: 'Graph', to: '/graph', icon: GitFork },
  { label: 'A/B Testing', to: '/ab-testing', icon: FlaskConical },
  { label: 'Learning', to: '/learning', icon: Brain },
  { label: 'Pipeline', to: '/pipeline', icon: Cpu },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">N</div>
          <div>
            <div className="logo-text">Neuro<span>Lead</span></div>
          </div>
        </div>
        <div className="logo-badge"><Zap size={9} style={{display:'inline',marginRight:3}}/>AI Intelligence System</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-group-label">Navigation</div>
        {NAV.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot">Backend online</div>
        <div style={{ marginTop: 4, fontSize: 11, opacity: 0.6 }}>P95.ai · NeuroLead v1.0</div>
      </div>
    </aside>
  );
}
