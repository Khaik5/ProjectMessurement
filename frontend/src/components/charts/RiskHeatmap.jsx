import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import EmptyState from '../common/EmptyState.jsx';
import { riskClass, riskFromProbability } from '../../utils/riskUtils.js';
import { fmtNumber, fmtPercent } from '../../utils/formatters.js';

const levels = ['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

function normalizeRows(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.rows)) return data.rows;
  if (Array.isArray(data?.heatmap)) {
    return data.heatmap.map((item) => ({
      module_name: item.x,
      defect_probability: item.value,
      risk_level: item.risk_level
    }));
  }
  return [];
}

export default function RiskHeatmap({ data = [] }) {
  const [filter, setFilter] = useState('ALL');
  const [tooltip, setTooltip] = useState(null);
  const rows = useMemo(() => normalizeRows(data), [data]);
  const filtered = useMemo(
    () => rows.filter((row) => filter === 'ALL' || (row.risk_level || riskFromProbability(row.defect_probability)) === filter),
    [rows, filter]
  );
  const highest = rows.reduce((best, row) => Number(row.defect_probability || 0) > Number(best?.defect_probability || 0) ? row : best, null);
  const avg = rows.length ? rows.reduce((sum, row) => sum + Number(row.defect_probability || 0), 0) / rows.length : 0;

  if (!rows.length) return <EmptyState title="No heatmap data" description="Run dataset analysis to populate risk cells." />;

  const columns = [
    ['Size', 'size_score'],
    ['Complexity', 'complexity_score'],
    ['Coupling', 'coupling_score'],
    ['Churn', 'churn_score'],
    ['Probability', 'defect_probability']
  ];

  return (
    <div>
      <div className="heatmap-toolbar">
        <div className="heatmap-summary">
          <span>{fmtNumber(rows.length)} modules</span>
          <span>Avg {fmtPercent(avg)}</span>
          <span>Peak {highest?.module_name || '-'} {fmtPercent(highest?.defect_probability)}</span>
        </div>
        <div className="heatmap-legend">
          {levels.map((level) => (
            <button
              key={level}
              className={`badge ${filter === level ? 'risk-medium' : ''}`}
              onClick={() => setFilter(level)}
              type="button"
            >
              {level !== 'ALL' ? <span className={`legend-dot dot-${level.toLowerCase()}`} /> : null}
              {level}
            </button>
          ))}
        </div>
      </div>

      <div className="matrix-wrap">
        <div className="matrix-row matrix-head">
          <span>Module</span>
          {columns.map(([label]) => <span key={label}>{label}</span>)}
        </div>
        {filtered.slice(0, 36).map((item, rowIndex) => {
          const level = item.risk_level || riskFromProbability(item.defect_probability);
          return (
            <motion.div
              key={`${item.module_name}-${rowIndex}`}
              className="matrix-row"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: rowIndex * 0.015, duration: 0.18 }}
            >
              <strong title={item.module_name}>{item.module_name}</strong>
              {columns.map(([, key]) => {
                const value = Number(item[key] || 0);
                const cellLevel = key === 'defect_probability' ? level : riskFromProbability(value);
                return (
                  <span
                    key={`${item.module_name}-${key}`}
                    className={`heat-cell ${riskClass(cellLevel)}`}
                    style={{ opacity: 0.58 + Math.min(value, 1) * 0.42 }}
                    onMouseEnter={(event) => setTooltip({ item, x: event.clientX + 12, y: event.clientY + 12 })}
                    onMouseMove={(event) => setTooltip((current) => current ? { ...current, x: event.clientX + 12, y: event.clientY + 12 } : null)}
                    onMouseLeave={() => setTooltip(null)}
                  >
                    {fmtPercent(value)}
                  </span>
                );
              })}
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {tooltip ? (
          <motion.div
            className="chart-tooltip"
            style={{ left: tooltip.x, top: tooltip.y }}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
          >
            <strong>{tooltip.item.module_name}</strong>
            <dl>
              <dt>Probability</dt><dd>{fmtPercent(tooltip.item.defect_probability)}</dd>
              <dt>Risk</dt><dd>{tooltip.item.risk_level || riskFromProbability(tooltip.item.defect_probability)}</dd>
              <dt>Risk score</dt><dd>{fmtPercent(tooltip.item.risk_score)}</dd>
              <dt>Complexity</dt><dd>{fmtNumber(tooltip.item.complexity)}</dd>
              <dt>Coupling</dt><dd>{fmtNumber(tooltip.item.coupling)}</dd>
              <dt>Churn</dt><dd>{fmtNumber(tooltip.item.code_churn)}</dd>
            </dl>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
