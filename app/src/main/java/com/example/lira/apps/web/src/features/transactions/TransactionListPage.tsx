import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, formatDate } from '../../lib/formatters';
import { ArrowLeftRight, Upload, Download, Search } from 'lucide-react';

export const TransactionListPage: React.FC = () => {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [directionFilter, setDirectionFilter] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const res = await api.getTransactions({
        direction: directionFilter || undefined,
        q: search || undefined
      });
      setTransactions(res.items || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [directionFilter]);

  const handleDownloadTemplate = () => {
    window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/transactions/csv-template`, '_blank');
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    try {
      setImporting(true);
      const formData = new FormData();
      formData.append('file', importFile);
      const res = await api.importTransactionsCsv(formData);
      setImportResult(res);
      await loadTransactions();
    } catch (err: any) {
      alert(`Import failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '12px', flex: 1, minWidth: '280px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="input"
                style={{ paddingLeft: '36px' }}
                placeholder="Search transaction ID, account ref, or fingerprint..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadTransactions()}
              />
            </div>

            <div style={{ width: '160px' }}>
              <select className="select" value={directionFilter} onChange={(e) => setDirectionFilter(e.target.value)}>
                <option value="">All Directions</option>
                <option value="outgoing">Outgoing</option>
                <option value="incoming">Incoming</option>
              </select>
            </div>

            <button className="btn btn-primary" onClick={loadTransactions}>Filter</button>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-sm" onClick={handleDownloadTemplate}>
              <Download size={14} /> Download CSV Template
            </button>
            <button className="btn btn-sm btn-primary" onClick={() => { setImportResult(null); setIsImportModalOpen(true); }}>
              <Upload size={14} /> Import CSV
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>External Ref</th>
                <th>Occurred At</th>
                <th>Direction</th>
                <th>Amount</th>
                <th>Supplier / Counterparty</th>
                <th>Beneficiary Fingerprint</th>
                <th>Channel Route</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading transactions...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No transactions found.
                  </td>
                </tr>
              ) : (
                transactions.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{t.external_id}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t.account_ref}</div>
                    </td>
                    <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(t.occurred_at)}
                    </td>
                    <td>
                      <span className={`badge ${t.direction === 'outgoing' ? 'badge-high' : 'badge-low'}`}>
                        {t.direction}
                      </span>
                    </td>
                    <td className="tabular-nums" style={{ fontWeight: 600 }}>
                      {formatCurrency(t.amount, t.currency)}
                    </td>
                    <td>
                      <div>{t.supplier_name || t.counterparty_ref || '—'}</div>
                    </td>
                    <td>
                      <span className="tabular-nums" style={{ fontSize: '12px' }}>
                        {t.beneficiary_fingerprint || '—'}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t.contact_route || 'unknown'}</td>
                    <td>
                      <span className="badge" style={{ background: 'var(--surface-muted)' }}>{t.source}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CSV Import Modal */}
      {isImportModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Import Transactions CSV</h3>
              <button className="btn btn-sm" onClick={() => setIsImportModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleImportSubmit}>
              <div className="form-group">
                <label className="form-label">Select CSV File</label>
                <input
                  type="file"
                  accept=".csv"
                  className="input"
                  onChange={(e) => setImportFile(e.target.files ? e.target.files[0] : null)}
                  required
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                  Required columns: external_id, occurred_at, direction, amount, currency, supplier_name, beneficiary_fingerprint, contact_route
                </div>
              </div>

              {importResult && (
                <div style={{ padding: '12px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '12px' }}>
                  <div style={{ color: 'var(--success)', fontWeight: 600 }}>
                    Successfully imported {importResult.imported_count} row(s).
                  </div>
                  {importResult.rejected_count > 0 && (
                    <div style={{ color: 'var(--danger)', marginTop: '4px' }}>
                      Rejected {importResult.rejected_count} row(s) due to validation errors.
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="btn" onClick={() => setIsImportModalOpen(false)}>Close</button>
                <button type="submit" className="btn btn-primary" disabled={importing || !importFile}>
                  {importing ? 'Validating & Importing...' : 'Import Records'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
