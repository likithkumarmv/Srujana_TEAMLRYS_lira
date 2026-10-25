import React from 'react';
import { RefreshCw, Radio, Database } from 'lucide-react';
import { api } from '../../lib/api';

interface NavbarProps {
  pageTitle: string;
  onRefresh?: () => void;
  isSeeding?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ pageTitle, onRefresh, isSeeding }) => {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text)' }}>
          {pageTitle}
        </h1>
      </div>

      <div className="topbar-right">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--success)' }}>
          <Radio size={14} className="animate-pulse" />
          <span style={{ fontWeight: 600 }}>Realtime Active</span>
        </div>

        <button
          className="btn btn-sm btn-primary"
          onClick={async () => {
            try {
              await api.seedDemo();
              if (onRefresh) onRefresh();
            } catch (e: any) {
              alert(`Seed error: ${e.message}`);
            }
          }}
          disabled={isSeeding}
        >
          <Database size={14} />
          <span>Reset / Reseed Demo</span>
        </button>

        {onRefresh && (
          <button className="btn btn-sm" onClick={onRefresh} title="Refresh data">
            <RefreshCw size={14} />
          </button>
        )}
      </div>
    </header>
  );
};
