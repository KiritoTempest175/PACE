import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Search, Code2, BookOpen, Globe2, HardDrive, Settings, X, ArrowRight } from 'lucide-react'

export function SearchModal({ isOpen, onClose, onOpenSettings }) {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        if (isOpen) onClose()
        else {
          // Trigger open via custom event
          window.dispatchEvent(new CustomEvent('pace-open-search'))
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const items = [
    { label: 'Coding Mastery Workspace', desc: 'Python & JS/TS dual-engine generator', path: '/coding', icon: Code2 },
    { label: 'Literacy Mastery Workspace', desc: 'NLP summarization & NLI factual verifier', path: '/literacy', icon: BookOpen },
    { label: 'Research Mastery Workspace', desc: 'Academic literature synthesis & citations', path: '/research', icon: Globe2 },
    { label: 'Hardware Telemetry Monitor', desc: 'Real-time VRAM allocation (8.0 GB max)', path: '/#hardware', icon: HardDrive },
    { label: 'System Preferences & Settings', desc: 'Adjust model speed, max VRAM, theme', action: 'settings', icon: Settings },
  ]

  const filtered = items.filter(
    (item) =>
      item.label.toLowerCase().includes(query.toLowerCase()) ||
      item.desc.toLowerCase().includes(query.toLowerCase())
  )

  const handleSelect = (item) => {
    onClose()
    if (item.action === 'settings') {
      onOpenSettings()
    } else {
      navigate(item.path)
    }
  }

  return (
    <AnimatePresence>
      <div className="modal-backdrop-overlay" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.96 }}
          transition={{ duration: 0.15 }}
          className="search-modal-card"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="search-input-header">
            <Search size={18} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              autoFocus
              className="search-input-field"
              placeholder="Search workspaces, benchmarks, or commands..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>

          <div className="search-results-list">
            {filtered.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No matching results found for "{query}"
              </div>
            ) : (
              filtered.map((item, idx) => {
                const Icon = item.icon
                return (
                  <div
                    key={idx}
                    className="search-result-item"
                    onClick={() => handleSelect(item)}
                  >
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--bg-canvas)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-primary)',
                      }}
                    >
                      <Icon size={16} />
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <strong style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{item.label}</strong>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.desc}</span>
                    </div>
                    <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                  </div>
                )
              })
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
