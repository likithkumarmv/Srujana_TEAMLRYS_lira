export function formatCurrency(amount: number | null | undefined, currency: string = 'INR'): string {
  if (amount === null || amount === undefined) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0
  }).format(amount);
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(d);
  } catch {
    return dateStr;
  }
}

export function getPriorityClass(priority: string): string {
  switch (priority.toLowerCase()) {
    case 'critical': return 'badge-critical';
    case 'high': return 'badge-high';
    case 'watch': return 'badge-watch';
    case 'low': return 'badge-low';
    default: return 'badge-low';
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'open': return 'Open';
    case 'awaiting_verification': return 'Awaiting Verification';
    case 'under_review': return 'Under Review';
    case 'escalated': return 'Escalated';
    case 'closed_verified': return 'Verified Legitimate';
    case 'closed_rejected': return 'Rejected (Fraud Prevented)';
    case 'closed_inconclusive': return 'Closed Inconclusive';
    default: return status;
  }
}
