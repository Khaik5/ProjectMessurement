export function riskClass(level) {
  return {
    LOW: 'risk-low',
    MEDIUM: 'risk-medium',
    HIGH: 'risk-high',
    CRITICAL: 'risk-critical'
  }[level] || 'risk-low';
}

export function riskFromProbability(probability) {
  const value = Number(probability) || 0;
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
