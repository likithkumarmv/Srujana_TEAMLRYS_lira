import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatDate } from '../../lib/formatters';
import {
  CreditCard,
  Cpu,
  Plus,
  Edit2,
  Trash2,
  Radio,
  CheckCircle2,
  XCircle,
  Smartphone,
  ShieldCheck,
  Search
} from 'lucide-react';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<any[]>([]);
  const [nfcCards, setNfcCards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Create / Edit modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCard, setEditingCard] = useState<any>(null);
  const [cardForm, setCardForm] = useState({
    card_uid: '',
    label: '',
    operator_name: '',
    operator_id: '',
    role: 'analyst',
    status: 'active',
    notes: ''
  });

  // Tap simulation state
  const [simUid, setSimUid] = useState('04:A2:3B:1C');
  const [simResult, setSimResult] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [devList, nfcList] = await Promise.all([
        api.getDevices(),
        api.listNfcCards(undefined, search || undefined)
      ]);
      setDevices(devList || []);
      setNfcCards(nfcList.items || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search]);

  const handleOpenCreateModal = () => {
    setEditingCard(null);
    setCardForm({
      card_uid: '',
      label: '',
      operator_name: '',
      operator_id: '',
      role: 'analyst',
      status: 'active',
      notes: ''
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (card: any) => {
    setEditingCard(card);
    setCardForm({
      card_uid: card.card_uid,
      label: card.label,
      operator_name: card.operator_name,
      operator_id: card.operator_id || '',
      role: card.role,
      status: card.status,
      notes: card.notes || ''
    });
    setIsModalOpen(true);
  };

  const handleSaveCard = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCard) {
        // Edit NFC Card
        await api.updateNfcCard(editingCard.id, {
          card_uid: cardForm.card_uid,
          label: cardForm.label,
          operator_name: cardForm.operator_name,
          operator_id: cardForm.operator_id || undefined,
          role: cardForm.role,
          status: cardForm.status,
          notes: cardForm.notes
        });
      } else {
        // Create NFC Card
        await api.createNfcCard({
          card_uid: cardForm.card_uid,
          label: cardForm.label,
          operator_name: cardForm.operator_name,
          operator_id: cardForm.operator_id || undefined,
          role: cardForm.role,
          status: cardForm.status,
          notes: cardForm.notes
        });
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err: any) {
      alert(`Failed to save NFC Card: ${err.message}`);
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!confirm('Are you sure you want to revoke/delete this NFC Card?')) return;
    try {
      await api.deleteNfcCard(cardId);
      await loadData();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleSimulateTap = async () => {
    try {
      setSimulating(true);
      const res = await api.scanNfcCard({
        card_uid: simUid,
        device_id: 'ESP32-Terminal-01',
        action: 'terminal_operator_tap'
      });
      setSimResult(res);
      await loadData();
    } catch (err: any) {
      alert(`Tap simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div>
      {/* ESP32 Physical Terminal Consoles */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">
            <Cpu size={18} />
            <span>ESP32 Physical Case Review Terminals</span>
          </h2>
          <span className="badge badge-simulated">2 Registered Hardware Nodes</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {devices.map((d) => (
            <div key={d.id} style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--surface-muted)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 600 }}>{d.device_name}</span>
                <span className={`badge ${d.is_online ? 'badge-low' : 'badge-high'}`}>
                  {d.is_online ? 'Online' : 'Offline / Stale'}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                <div>Firmware: {d.firmware_version}</div>
                <div>Last Heartbeat: {formatDate(d.last_seen_at)}</div>
                <div style={{ marginTop: '4px', fontStyle: 'italic' }}>Controls: 5-Button Console + ILI9341 TFT + RC522 Reader</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* NFC / RFID Cards Section (User's explicit requirement: Store NFC Create as well as Edit) */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="card-title">
              <CreditCard size={18} />
              <span>NFC / RFID Operator Badges & Keycards</span>
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Full database persistence for creating and editing operator NFC tags, role permissions, and terminal access.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ position: 'relative', width: '220px' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="input"
                style={{ paddingLeft: '30px', padding: '6px 30px' }}
                placeholder="Search NFC cards..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <button className="btn btn-sm btn-primary" onClick={handleOpenCreateModal}>
              <Plus size={14} /> Register New NFC Card
            </button>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Card UID</th>
                <th>Badge Label</th>
                <th>Assigned Operator</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Scanned</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    Loading NFC cards...
                  </td>
                </tr>
              ) : nfcCards.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No NFC cards found. Click "Register New NFC Card" to store a badge.
                  </td>
                </tr>
              ) : (
                nfcCards.map((card) => (
                  <tr key={card.id}>
                    <td>
                      <span className="tabular-nums" style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--primary)' }}>
                        {card.card_uid}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{card.label}</div>
                      {card.notes && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{card.notes}</div>}
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{card.operator_name}</div>
                      {card.operator_id && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{card.operator_id}</div>}
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'var(--surface-muted)' }}>
                        {card.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${card.status === 'active' ? 'badge-low' : 'badge-high'}`}>
                        {card.status}
                      </span>
                    </td>
                    <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {card.last_scanned_at ? (
                        <div>
                          <div>{formatDate(card.last_scanned_at)}</div>
                          <div style={{ fontSize: '10px' }}>{card.last_scanned_device}</div>
                        </div>
                      ) : (
                        'Never'
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button className="btn btn-sm" onClick={() => handleOpenEditModal(card)} title="Edit NFC Card Details">
                          <Edit2 size={12} /> Edit
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteCard(card.id)} title="Delete / Revoke">
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* NFC Tap & Scan Simulation Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Smartphone size={18} />
            <span>NFC Card Tap / Scan Simulator</span>
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Simulates physical RC522 or Android NFC tap against LIRA backend
          </span>
        </div>

        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ width: '220px' }}>
            <label className="form-label">Select Card UID to Tap</label>
            <select className="select" value={simUid} onChange={(e) => setSimUid(e.target.value)}>
              {nfcCards.map((c) => (
                <option key={c.id} value={c.card_uid}>
                  {c.card_uid} — {c.operator_name} ({c.status})
                </option>
              ))}
              <option value="FF:FF:FF:FF">FF:FF:FF:FF (Unregistered Card)</option>
            </select>
          </div>

          <div style={{ alignSelf: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleSimulateTap} disabled={simulating}>
              <Radio size={14} /> {simulating ? 'Scanning Tag...' : 'Simulate Card Tap'}
            </button>
          </div>
        </div>

        {simResult && (
          <div style={{ marginTop: '16px', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: simResult.authenticated ? 'rgba(35, 122, 87, 0.08)' : 'rgba(180, 35, 50, 0.08)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: simResult.authenticated ? 'var(--success)' : 'var(--danger)' }}>
              {simResult.authenticated ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
              <span>{simResult.message}</span>
            </div>
            {simResult.authenticated && (
              <div style={{ fontSize: '12px', marginTop: '6px', color: 'var(--text-muted)' }}>
                Verified Operator: <strong>{simResult.operator_name}</strong> | Role: <strong>{simResult.role.toUpperCase()}</strong> | Status: <strong>{simResult.status}</strong>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal for Creating or Editing NFC Card */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
                {editingCard ? 'Edit NFC Operator Card' : 'Register New NFC Operator Card'}
              </h3>
              <button className="btn btn-sm" onClick={() => setIsModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleSaveCard}>
              <div className="form-group">
                <label className="form-label">Card UID / Hardware Serial *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. 04:A2:3B:1C or 04:99:AA:BB"
                  value={cardForm.card_uid}
                  onChange={(e) => setCardForm({ ...cardForm, card_uid: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Badge Label *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Operations Desk 1 Card"
                  value={cardForm.label}
                  onChange={(e) => setCardForm({ ...cardForm, label: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Assigned Operator Name *</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. Sarah Jenkins"
                    value={cardForm.operator_name}
                    onChange={(e) => setCardForm({ ...cardForm, operator_name: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Employee / Staff ID</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. EMP-1044"
                    value={cardForm.operator_id}
                    onChange={(e) => setCardForm({ ...cardForm, operator_id: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Role Authorization *</label>
                  <select
                    className="select"
                    value={cardForm.role}
                    onChange={(e) => setCardForm({ ...cardForm, role: e.target.value })}
                  >
                    <option value="analyst">Analyst</option>
                    <option value="supervisor">Supervisor</option>
                    <option value="admin">Administrator</option>
                    <option value="operator">Terminal Operator</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Card Status *</label>
                  <select
                    className="select"
                    value={cardForm.status}
                    onChange={(e) => setCardForm({ ...cardForm, status: e.target.value })}
                  >
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="revoked">Revoked</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Notes & Department Assignment</label>
                <textarea
                  className="textarea"
                  rows={3}
                  placeholder="Add operational notes or department tags..."
                  value={cardForm.notes}
                  onChange={(e) => setCardForm({ ...cardForm, notes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button type="button" className="btn" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">
                  {editingCard ? 'Update NFC Card' : 'Save & Register NFC Card'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
