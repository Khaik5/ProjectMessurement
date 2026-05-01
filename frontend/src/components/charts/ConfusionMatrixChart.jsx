import EmptyState from '../common/EmptyState.jsx';

export default function ConfusionMatrixChart({ matrix }) {
  if (!matrix) return <EmptyState title="No confusion matrix" description="Train a model to see confusion matrix." />;
  
  const cells = [
    { label: 'TN', value: matrix?.[0]?.[0] ?? 0, desc: 'True Negative', color: '#10b981' },
    { label: 'FP', value: matrix?.[0]?.[1] ?? 0, desc: 'False Positive', color: '#f59e0b' },
    { label: 'FN', value: matrix?.[1]?.[0] ?? 0, desc: 'False Negative', color: '#ef4444' },
    { label: 'TP', value: matrix?.[1]?.[1] ?? 0, desc: 'True Positive', color: '#3b82f6' }
  ];
  
  return (
    <div style={{ padding: '16px' }}>
      <div className="matrix-grid" style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        maxWidth: '400px',
        margin: '0 auto'
      }}>
        {cells.map(({ label, value, desc, color }) => (
          <div 
            key={label}
            style={{
              padding: '20px',
              borderRadius: '12px',
              border: `2px solid ${color}`,
              backgroundColor: `${color}10`,
              textAlign: 'center',
              transition: 'transform 0.2s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600', 
              color: '#64748b',
              marginBottom: '4px'
            }}>
              {label}
            </div>
            <div style={{ 
              fontSize: '28px', 
              fontWeight: '700', 
              color: color,
              marginBottom: '4px'
            }}>
              {value}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: '#94a3b8'
            }}>
              {desc}
            </div>
          </div>
        ))}
      </div>
      <div style={{
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f8fafc',
        borderRadius: '8px',
        fontSize: '13px',
        color: '#64748b',
        textAlign: 'center'
      }}>
        <strong>Total Predictions:</strong> {cells.reduce((sum, c) => sum + c.value, 0)}
      </div>
    </div>
  );
}
