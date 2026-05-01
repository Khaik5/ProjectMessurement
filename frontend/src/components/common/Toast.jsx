import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const icons = {
  success: CheckCircle2,
  error: TriangleAlert,
  warning: TriangleAlert,
  info: Info
};

export default function Toast({ message, type = 'info', onClose }) {
  const Icon = icons[type] || Info;
  return (
    <AnimatePresence>
      {message ? (
        <motion.div
          className={`toast toast-${type}`}
          initial={{ opacity: 0, y: -10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.98 }}
          transition={{ duration: 0.18 }}
        >
          <Icon size={18} />
          <span>{message}</span>
          <button onClick={onClose} aria-label="Close notification"><X size={16} /></button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
