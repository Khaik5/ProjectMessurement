import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';
import { fmtPercent } from '../../utils/formatters.js';

const MODEL_LABELS = {
  'logistic_regression': 'Logistic Regression',
  'random_forest': 'Random Forest',
  'neural_network': 'Neural Network'
};

export default function ModelComparisonChart({ data = [] }) {
  if (!data.length) return <EmptyState title="No model comparison" description="Train models to populate MLModels and TrainingRuns." />;
  
  // Transform data to have readable labels
  const chartData = data.map(item => ({
    ...item,
    model: MODEL_LABELS[item.model_type] || item.model || item.model_type
  }));
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis 
          dataKey="model" 
          tick={{ fontSize: 12, fill: '#64748b' }}
          angle={-15}
          textAnchor="end"
          height={80}
        />
        <YAxis 
          domain={[0, 1]} 
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          tick={{ fontSize: 12, fill: '#64748b' }}
        />
        <Tooltip 
          formatter={(v) => fmtPercent(v)}
          contentStyle={{ 
            backgroundColor: '#fff', 
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '12px'
          }}
        />
        <Legend 
          wrapperStyle={{ paddingTop: '20px' }}
          iconType="rect"
        />
        <Bar dataKey="accuracy" fill="#3b82f6" name="Accuracy" radius={[4, 4, 0, 0]} />
        <Bar dataKey="precision" fill="#8b5cf6" name="Precision" radius={[4, 4, 0, 0]} />
        <Bar dataKey="recall" fill="#f59e0b" name="Recall" radius={[4, 4, 0, 0]} />
        <Bar dataKey="f1_score" fill="#10b981" name="F1-Score" radius={[4, 4, 0, 0]} />
        <Bar dataKey="roc_auc" fill="#2563eb" name="ROC-AUC" radius={[4, 4, 0, 0]} />
        <Bar dataKey="pr_auc" fill="#14b8a6" name="PR-AUC" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
