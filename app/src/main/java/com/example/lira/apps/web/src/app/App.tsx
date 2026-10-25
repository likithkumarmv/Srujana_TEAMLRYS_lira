import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { Navbar } from '../components/layout/Navbar';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { CaseListPage } from '../features/investigations/CaseListPage';
import { CaseDetailPage } from '../features/investigations/CaseDetailPage';
import { TransactionListPage } from '../features/transactions/TransactionListPage';
import { SupplierListPage } from '../features/suppliers/SupplierListPage';
import { VerificationQueuePage } from '../features/verification/VerificationQueuePage';
import { SimulatorPage } from '../features/simulator/SimulatorPage';
import { DevicesPage } from '../features/devices/DevicesPage';
import { AuditLogPage } from '../features/audit/AuditLogPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('lira_theme') as 'light' | 'dark') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('lira_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Realtime subscription setup
  useEffect(() => {
    if (!isSupabaseConfigured) return;
    try {
      const channel = supabase
        .channel('lira-changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'cases' }, () => {
          // Trigger refresh trigger
        })
        .subscribe();

      return () => {
        supabase.removeChannel(channel);
      };
    } catch (e) {
      console.warn('Realtime subscription fallback:', e);
    }
  }, []);

  const getPageTitle = () => {
    if (selectedCaseId && currentTab === 'investigations') return 'Investigation Workbench';
    switch (currentTab) {
      case 'dashboard': return 'Executive Financial Risk Console';
      case 'investigations': return 'Investigation Cases';
      case 'transactions': return 'Transaction Ledger & Batch Import';
      case 'suppliers': return 'Trusted Supplier Directory';
      case 'verification': return 'AI Supplier Call Verification Queue';
      case 'simulator': return 'Risk Engine Simulation Sandbox';
      case 'devices': return 'ESP32 Terminals & NFC Badges';
      case 'audit': return 'Compliance & Operator Audit Trail';
      case 'settings': return 'System Settings & Rule Weights';
      default: return 'LIRA Platform';
    }
  };

  const handleSelectTab = (tab: string) => {
    setSelectedCaseId(null);
    setCurrentTab(tab);
  };

  const handleNavigateToCase = (caseId: string) => {
    setSelectedCaseId(caseId);
    setCurrentTab('investigations');
  };

  return (
    <div className="app-container">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <div className="main-content">
        <Navbar pageTitle={getPageTitle()} />

        <main className="page-wrapper">
          {currentTab === 'dashboard' && (
            <DashboardPage
              onNavigateToCase={handleNavigateToCase}
              onNavigateTab={handleSelectTab}
            />
          )}

          {currentTab === 'investigations' && (
            selectedCaseId ? (
              <CaseDetailPage
                caseId={selectedCaseId}
                onBack={() => setSelectedCaseId(null)}
              />
            ) : (
              <CaseListPage onSelectCase={handleNavigateToCase} />
            )
          )}

          {currentTab === 'transactions' && <TransactionListPage />}

          {currentTab === 'suppliers' && <SupplierListPage />}

          {currentTab === 'verification' && <VerificationQueuePage />}

          {currentTab === 'simulator' && (
            <SimulatorPage onOpenCase={handleNavigateToCase} />
          )}

          {currentTab === 'devices' && <DevicesPage />}

          {currentTab === 'audit' && <AuditLogPage />}

          {currentTab === 'settings' && (
            <SettingsPage theme={theme} onToggleTheme={toggleTheme} />
          )}
        </main>
      </div>
    </div>
  );
};
