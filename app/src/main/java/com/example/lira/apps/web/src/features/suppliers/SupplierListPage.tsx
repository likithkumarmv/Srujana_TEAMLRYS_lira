import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, formatDate } from '../../lib/formatters';
import { Building2, ShieldCheck, AlertCircle, Phone } from 'lucide-react';

export const SupplierListPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      const res = await api.getSuppliers();
      setSuppliers(res.items || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuppliers();
  }, []);

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
          <ShieldCheck size={16} color="var(--primary)" />
          <span>LIRA maintains trusted vendor profiles. AI verification calls only connect using verified directory phone numbers, never untrusted invoice contacts.</span>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Vendor Organization</th>
                <th>Trusted Contact Directory</th>
                <th>Current Destination Fingerprint</th>
                <th>Established Baseline Fingerprint</th>
                <th>Independent Verification</th>
                <th>Ledger Volume</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading supplier directory...
                  </td>
                </tr>
              ) : (
                suppliers.map((s) => {
                  const isChanged = s.previous_beneficiary_fingerprint && s.current_beneficiary_fingerprint !== s.previous_beneficiary_fingerprint;
                  return (
                    <tr key={s.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{s.display_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Source: {s.trusted_contact_source}</div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Phone size={12} color="var(--primary)" />
                          <span style={{ fontWeight: 500 }}>{s.known_contact_name || 'Contact Office'}</span>
                        </div>
                        <div className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {s.masked_phone || 'Unverified'}
                        </div>
                      </td>
                      <td>
                        <span className="tabular-nums" style={{ fontWeight: 600, color: isChanged ? 'var(--danger)' : 'var(--text)' }}>
                          {s.current_beneficiary_fingerprint || 'Pending'}
                        </span>
                      </td>
                      <td>
                        <span className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {s.previous_beneficiary_fingerprint || 'Initial Profile'}
                        </span>
                      </td>
                      <td>
                        {s.last_independently_verified_at ? (
                          <div style={{ fontSize: '12px', color: 'var(--success)' }}>
                            Verified {formatDate(s.last_independently_verified_at)}
                          </div>
                        ) : (
                          <span className="badge badge-high">Unverified Freshness</span>
                        )}
                      </td>
                      <td className="tabular-nums" style={{ fontWeight: 600 }}>
                        {formatCurrency(s.total_volume)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
