export const fmtPercent = (value, digits = 1) => `${((Number(value) || 0) * 100).toFixed(digits)}%`;
export const fmtNumber = (value) => new Intl.NumberFormat('en').format(Number(value) || 0);
export const fmtDate = (value) => (value ? new Intl.DateTimeFormat('en', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) : '-');
