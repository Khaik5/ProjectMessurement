import { motion } from 'framer-motion';

export default function Card({ children, className = '', interactive = false }) {
  return (
    <motion.section
      className={`card ${interactive ? 'card-interactive' : ''} ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
    >
      {children}
    </motion.section>
  );
}
