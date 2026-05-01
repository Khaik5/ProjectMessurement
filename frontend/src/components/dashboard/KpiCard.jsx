import { motion } from 'framer-motion';

export default function KpiCard({ label, value, helper, icon: Icon, tone = 'neutral' }) {
  return (
    <motion.div className={`kpi-card tone-${tone}`} whileHover={{ y: -3 }} transition={{ duration: 0.18 }}>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {helper ? <small>{helper}</small> : null}
      </div>
      {Icon ? <Icon size={24} /> : null}
    </motion.div>
  );
}
