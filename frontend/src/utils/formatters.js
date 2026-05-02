export const normalizeProbability = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  const scaled = numeric > 1 && numeric <= 100 ? numeric / 100 : numeric;
  return Math.min(Math.max(scaled, 0), 1);
};

export const fmtPercent = (value, digits = 1) => `${(normalizeProbability(value) * 100).toFixed(digits)}%`;
export const fmtNumber = (value) => new Intl.NumberFormat('en').format(Number(value) || 0);
export const fmtDate = (value) => (value ? new Intl.DateTimeFormat('en', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) : '-');
