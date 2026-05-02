export function riskClass(level) {
  return {
    LOW: 'risk-low',
    MEDIUM: 'risk-medium',
    HIGH: 'risk-high',
    CRITICAL: 'risk-critical'
  }[level] || 'risk-low';
}

export function riskFromProbability(probability) {
  const numeric = Number(probability) || 0;
  const value = numeric > 1 && numeric <= 100 ? numeric / 100 : Math.min(Math.max(numeric, 0), 1);
  if (value >= 0.8) return 'CRITICAL';
  if (value >= 0.6) return 'HIGH';
  if (value >= 0.3) return 'MEDIUM';
  return 'LOW';
}

export function predictionClass(label) {
  return {
    'No Defect': 'prediction-safe',
    'Possible Defect': 'prediction-warning',
    Defect: 'prediction-defect'
  }[label] || '';
}
