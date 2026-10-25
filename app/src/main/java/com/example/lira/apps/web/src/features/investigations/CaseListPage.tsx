import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, formatDate, getPriorityClass, getStatusLabel } from '../../lib/formatters';
import { ShieldAlert, Search, Filter, ArrowRight } from 'lucide-react';

interface CaseListPageProps {
  onSelectCase: (caseId: string) => void;
}

export const CaseListPage: React.FC<CaseListPageProps> = ({ onSelectCase }) => {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  const loadCases = async () => {
    try {
      setLoading(true);
      const res = await api.getCases({
        q: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined
      });
      setCases(res.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, priorityFilter]);

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input"
              style={{ paddingLeft: '36px' }}
              placeholder="Search by case ref, title, or vendor..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadCases()}
            />
          </div>

          <div style={{ width: '180px' }}>
            <select className="select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="awaiting_verification">Awaiting Verification</option>
              <option value="under_review">Under Review</option>
              <option value="escalated">Escalated</option>
              <option value="closed_verified">Closed Verified</option>
              <option value="closed_rejected">Closed Rejected</option>
            </select>
          </div>

          <div style={{ width: '160px' }}>
            <select className="select" value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
              <option value="">All Priorities</option>
              <option value="critical">Critical (75–100)</option>
              <option value="high">High (50–74)</option>
              <option value="watch">Watch (25–49)</option>
              <option value="low">Low (0–24)</option>
            </select>
          </div>

          <button className="btn btn-primary" onClick={loadCases}>
            Filter
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Case Identifier</th>
                <th>Priority</th>
                <th>Risk Score</th>
                <th>Status</th>
                <th>Amount At Risk</th>
                <th>Last Updated</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading cases...
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No investigation cases found matching filter criteria.
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text)' }}>{c.case_ref}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{c.title}</div>
                    </td>
                    <td>
                      <span className={`badge ${getPriorityClass(c.priority)}`}>
                        {c.priority}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 700 }} className="tabular-nums">{c.risk_score}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}> / 100</span>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px' }}>{getStatusLabel(c.status)}</span>
                    </td>
                    <td className="tabular-nums" style={{ fontWeight: 600 }}>
                      {formatCurrency(c.amount_at_risk)}
                    </td>
                    <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(c.updated_at)}
                    </td>
                    <td>
                      <button className="btn btn-sm btn-primary" onClick={() => onSelectCase(c.id)}>
                        Workbench <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
