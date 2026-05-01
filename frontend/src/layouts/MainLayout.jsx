import { Outlet, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

import Header from '../components/layout/Header.jsx';
import Sidebar from '../components/layout/Sidebar.jsx';
import Toast from '../components/common/Toast.jsx';

export default function MainLayout() {
  const location = useLocation();
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const handler = (event) => setToast(event.detail || null);
    window.addEventListener('defectai:toast', handler);
    return () => window.removeEventListener('defectai:toast', handler);
  }, []);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-region">
        <Header pathname={location.pathname} />
        <main className="page-content">
          <AnimatePresence mode="wait">
            <motion.div
              className="page-frame"
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
        <Toast message={toast?.message} type={toast?.type || 'info'} onClose={() => setToast(null)} />
      </div>
    </div>
  );
}
