import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatDate } from '../../lib/formatters';
import { ClipboardList, Shield, Filter } from 'lucide-react';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');

  const loadAudit = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditLogs({ action: actionFilter || undefined });
      setLogs(res.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, [actionFilter]);

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ flex: 1, maxWidth: '300px' }}>
            <input
              type="text"
              className="input"
              placeholder="Filter by action (e.g. nfc, case, call)..."
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={loadAudit}>Filter</button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <ClipboardList size={18} />
            <span>Append-Only Compliance & Operator Audit Trail</span>
          </h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Non-repudiation ledger</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor Type</th>
                <th>Action</th>
                <th>Target Object</th>
                <th>Request ID</th>
                <th>Event Payload Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No audit log records found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(log.created_at)}
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'var(--surface-muted)' }}>
                        {log.actor_type}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{log.action}</span>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {log.object_type}
                    </td>
                    <td className="tabular-nums" style={{ fontSize: '11px', fontFamily: 'monospace' }}>
                      {log.request_id || '—'}
                    </td>
                    <td style={{ fontSize: '12px', maxWidth: '340px', wordBreak: 'break-word' }}>
                      {JSON.stringify(log.details)}
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
