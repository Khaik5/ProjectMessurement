import { AlertTriangle, CheckCircle2, ShieldCheck, Target, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';

import EmptyState from '../common/EmptyState.jsx';

function normalizeMatrix(matrix) {
  if (matrix && typeof matrix === 'object' && !Array.isArray(matrix)) {
    return {
      tn: Number(matrix.tn || 0),
      fp: Number(matrix.fp || 0),
      fn: Number(matrix.fn || 0),
      tp: Number(matrix.tp || 0)
    };
  }
  if (!Array.isArray(matrix) || matrix.length < 2) return null;
  return {
    tn: Number(matrix?.[0]?.[0] || 0),
    fp: Number(matrix?.[0]?.[1] || 0),
    fn: Number(matrix?.[1]?.[0] || 0),
    tp: Number(matrix?.[1]?.[1] || 0)
  };
}

function safeRatio(numerator, denominator) {
  return denominator ? numerator / denominator : 0;
}

function formatPct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

export default function ConfusionMatrixChart({ matrix, metrics = {}, subtitle = 'Active production model' }) {
  const values = normalizeMatrix(matrix);
  if (!values) {
    return <EmptyState title="No confusion matrix" description="Train a production model to populate model diagnostics." />;
  }

  const total = values.tn + values.fp + values.fn + values.tp;
  const fallbackPrecision = safeRatio(values.tp, values.tp + values.fp);
  const fallbackRecall = safeRatio(values.tp, values.tp + values.fn);
  const metricCards = [
    { label: 'Accuracy', value: metrics.accuracy ?? safeRatio(values.tp + values.tn, total) },
    { label: 'Precision', value: metrics.precision ?? fallbackPrecision },
    { label: 'Recall', value: metrics.recall ?? fallbackRecall },
    { label: 'F1', value: metrics.f1 ?? safeRatio(2 * fallbackPrecision * fallbackRecall, fallbackPrecision + fallbackRecall) }
  ];

  const quadrants = [
    {
      key: 'TN',
      title: 'True Negative',
      value: values.tn,
      tone: 'tn',
      icon: ShieldCheck,
      actual: 'Actual Negative',
      predicted: 'Predicted Negative'
    },
    {
      key: 'FP',
      title: 'False Positive',
      value: values.fp,
      tone: 'fp',
      icon: AlertTriangle,
      actual: 'Actual Negative',
      predicted: 'Predicted Positive'
    },
    {
      key: 'FN',
      title: 'False Negative',
      value: values.fn,
      tone: 'fn',
      icon: XCircle,
      actual: 'Actual Positive',
      predicted: 'Predicted Negative'
    },
    {
      key: 'TP',
      title: 'True Positive',
      value: values.tp,
      tone: 'tp',
      icon: Target,
      actual: 'Actual Positive',
      predicted: 'Predicted Positive'
    }
  ];

  return (
    <motion.section className="cmx-card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.24 }}>
      <div className="cmx-header">
        <div>
          <h4>Confusion Matrix</h4>
          <p>{subtitle}</p>
        </div>
        <span className="cmx-total"><CheckCircle2 size={15} />{total} total</span>
      </div>

      <div className="cmx-metrics">
        {metricCards.map((item) => (
          <div className="cmx-metric" key={item.label}>
            <span>{item.label}</span>
            <strong>{formatPct(item.value)}</strong>
          </div>
        ))}
      </div>

      <div className="cmx-layout" aria-label="Confusion matrix">
        <span className="cmx-corner">Actual / Predicted</span>
        <span className="cmx-col">Negative</span>
        <span className="cmx-col">Positive</span>
        <span className="cmx-row cmx-row-negative">Negative</span>
        <span className="cmx-row cmx-row-positive">Positive</span>

        {quadrants.map((cell, index) => {
          const Icon = cell.icon;
          return (
            <motion.article
              className={`cmx-cell cmx-${cell.tone}`}
              key={cell.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.045, duration: 0.22 }}
              whileHover={{ y: -3 }}
            >
              <div className="cmx-cell-top">
                <span className="cmx-code">{cell.key}</span>
                <Icon size={18} />
              </div>
              <strong>{cell.value}</strong>
              <span>{cell.title}</span>
              <small>{cell.actual} · {cell.predicted}</small>
            </motion.article>
          );
        })}
      </div>
    </motion.section>
  );
}
