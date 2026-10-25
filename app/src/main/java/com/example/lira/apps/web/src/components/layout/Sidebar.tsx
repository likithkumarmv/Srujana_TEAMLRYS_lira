import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  ArrowLeftRight,
  Building2,
  PhoneCall,
  FlaskConical,
  CreditCard,
  ClipboardList,
  Settings,
  Shield,
  Sun,
  Moon
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  theme: string;
  onToggleTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  theme,
  onToggleTheme
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'investigations', label: 'Investigations', icon: ShieldAlert },
    { id: 'transactions', label: 'Transactions', icon: ArrowLeftRight },
    { id: 'suppliers', label: 'Suppliers', icon: Building2 },
    { id: 'verification', label: 'Call Verification', icon: PhoneCall },
    { id: 'simulator', label: 'Risk Simulator', icon: FlaskConical },
    { id: 'devices', label: 'Devices & NFC Cards', icon: CreditCard },
    { id: 'audit', label: 'Audit Trail', icon: ClipboardList },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-badge">
          <Shield size={16} />
          <span>LIRA</span>
        </div>
        <span className="logo-title">Risk Defense</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(item.id)}
            >
              <Icon size={18} />
              <span className="nav-label">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-sm"
          onClick={onToggleTheme}
          style={{ width: '100%', justifyContent: 'flex-start' }}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>

        <div style={{ fontSize: '11px', color: 'var(--text-muted)', padding: '0 4px' }}>
          <div>Acme FinTech Corp</div>
          <div style={{ fontWeight: 600, color: 'var(--text)' }}>Supervisor Console</div>
        </div>
      </div>
    </aside>
  );
};
