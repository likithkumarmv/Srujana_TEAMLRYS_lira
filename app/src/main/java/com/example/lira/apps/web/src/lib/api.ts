const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('lira_token') || 'dev-role:supervisor';
  const headers: Record<string, string> = {
    'Authorization': `Bearer ${token}`,
    ...((options.headers as Record<string, string>) || {})
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (!res.ok) {
    let errPayload = { error: { message: `Request failed with HTTP ${res.status}` } };
    try {
      errPayload = await res.json();
    } catch {}
    throw new Error(errPayload.error?.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Dashboard & Auth
  getDashboardSummary: () => fetchJson<any>('/api/v1/dashboard/summary'),
  getMe: () => fetchJson<any>('/api/v1/me'),
  seedDemo: () => fetchJson<any>('/api/v1/demo/seed', { method: 'POST' }),

  // Cases
  getCases: (params?: { status?: string; priority?: string; q?: string }) => {
    const qp = new URLSearchParams();
    if (params?.status) qp.append('status', params.status);
    if (params?.priority) qp.append('priority', params.priority);
    if (params?.q) qp.append('q', params.q);
    return fetchJson<any>(`/api/v1/cases?${qp.toString()}`);
  },
  getCaseDetail: (caseId: string) => fetchJson<any>(`/api/v1/cases/${caseId}`),
  acknowledgeCase: (caseId: string, note?: string) =>
    fetchJson<any>(`/api/v1/cases/${caseId}/actions/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ note: note || 'Acknowledged by operator' })
    }),
  escalateCase: (caseId: string, reason: string, version: number) =>
    fetchJson<any>(`/api/v1/cases/${caseId}/actions/escalate`, {
      method: 'POST',
      body: JSON.stringify({ reason, version })
    }),
  setCaseDisposition: (caseId: string, disposition: string, note: string, version: number) =>
    fetchJson<any>(`/api/v1/cases/${caseId}/disposition`, {
      method: 'POST',
      body: JSON.stringify({ disposition, note, version })
    }),
  requestVerificationCall: (caseId: string, note?: string) =>
    fetchJson<any>(`/api/v1/cases/${caseId}/verification-calls`, {
      method: 'POST',
      body: JSON.stringify({ note: note || 'Verification requested by analyst' })
    }),

  // Transactions & CSV
  getTransactions: (params?: { direction?: string; q?: string }) => {
    const qp = new URLSearchParams();
    if (params?.direction) qp.append('direction', params.direction);
    if (params?.q) qp.append('q', params.q);
    return fetchJson<any>(`/api/v1/transactions?${qp.toString()}`);
  },
  importTransactionsCsv: (formData: FormData) =>
    fetchJson<any>('/api/v1/transactions/import-csv', {
      method: 'POST',
      body: formData
    }),

  // Suppliers
  getSuppliers: () => fetchJson<any>('/api/v1/suppliers'),
  getSupplierDetail: (id: string) => fetchJson<any>(`/api/v1/suppliers/${id}`),

  // Verification Calls
  getVerificationCalls: () => fetchJson<any>('/api/v1/verification-calls'),

  // Simulations
  runSimulation: (scenarioKey: string, persist: boolean = true) =>
    fetchJson<any>('/api/v1/simulations/run', {
      method: 'POST',
      body: JSON.stringify({ scenario_key: scenarioKey, persist })
    }),

  // Devices & Hardware
  getDevices: () => fetchJson<any>('/api/v1/devices'),

  // NFC Card Management (Create, Edit, List, and Tap Simulation)
  listNfcCards: (status?: string, q?: string) => {
    const qp = new URLSearchParams();
    if (status) qp.append('status', status);
    if (q) qp.append('q', q);
    return fetchJson<any>(`/api/v1/nfc-cards?${qp.toString()}`);
  },
  createNfcCard: (data: {
    card_uid: string;
    label: string;
    operator_name: string;
    operator_id?: string;
    role: string;
    status: string;
    notes?: string;
  }) =>
    fetchJson<any>('/api/v1/nfc-cards', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateNfcCard: (cardId: string, data: any) =>
    fetchJson<any>(`/api/v1/nfc-cards/${cardId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  deleteNfcCard: (cardId: string) =>
    fetchJson<any>(`/api/v1/nfc-cards/${cardId}`, {
      method: 'DELETE'
    }),
  scanNfcCard: (payload: { card_uid: string; device_id?: string; action?: string; case_id?: string }) =>
    fetchJson<any>('/api/v1/nfc-cards/scan', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),

  // Gemini AI Intelligence
  getGeminiStatus: () => fetchJson<any>('/api/v1/gemini/status'),
  analyzeCaseWithGemini: (caseId: string) =>
    fetchJson<any>('/api/v1/gemini/analyze-case', {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId })
    }),

  // Audit Logs
  getAuditLogs: (params?: { action?: string; actor_type?: string }) => {
    const qp = new URLSearchParams();
    if (params?.action) qp.append('action', params.action);
    if (params?.actor_type) qp.append('actor_type', params.actor_type);
    return fetchJson<any>(`/api/v1/audit?${qp.toString()}`);
  }
};
