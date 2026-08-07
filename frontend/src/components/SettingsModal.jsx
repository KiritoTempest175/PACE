import { motion, AnimatePresence } from 'framer-motion'
import { X, Settings, Cpu, Moon, Sun, Check, HardDrive } from 'lucide-react'
import { useTheme } from '../ThemeContext'

export function SettingsModal({ isOpen, onClose }) {
  const { theme, toggleTheme } = useTheme()

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="modal-backdrop-overlay" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          className="search-modal-card"
          style={{ maxWidth: '520px' }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="search-input-header" style={{ justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Settings size={20} style={{ color: 'var(--accent-primary)' }} />
              <strong style={{ fontSize: '16px', color: 'var(--text-primary)' }}>System Preferences</strong>
            </div>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>

          <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Theme Configuration */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Appearance Theme
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <button
                  onClick={() => theme !== 'dark' && toggleTheme()}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: theme === 'dark' ? 'var(--accent-soft)' : 'var(--bg-canvas)',
                    border: theme === 'dark' ? '1px solid var(--border-accent)' : '1px solid var(--border-subtle)',
                    color: theme === 'dark' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  <Moon size={16} />
                  <span>Dark Enterprise</span>
                  {theme === 'dark' && <Check size={14} />}
                </button>

                <button
                  onClick={() => theme !== 'light' && toggleTheme()}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: theme === 'light' ? 'var(--accent-soft)' : 'var(--bg-canvas)',
                    border: theme === 'light' ? '1px solid var(--border-accent)' : '1px solid var(--border-subtle)',
                    color: theme === 'light' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  <Sun size={16} />
                  <span>Light Studio</span>
                  {theme === 'light' && <Check size={14} />}
                </button>
              </div>
            </div>

            {/* Hardware VRAM Ceiling */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Hardware VRAM Limits
              </label>
              <div
                style={{
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <HardDrive size={18} style={{ color: 'var(--status-emerald)' }} />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>8.0 GB VRAM Cap</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Optimized for single-GPU local execution</span>
                  </div>
                </div>
                <span className="badge-vram-limit">Active</span>
              </div>
            </div>

            {/* Local Backend Endpoint */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                API Endpoint
              </label>
              <input
                type="text"
                readOnly
                value="http://127.0.0.1:8000/api"
                style={{
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 14px',
                  color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                }}
              />
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
