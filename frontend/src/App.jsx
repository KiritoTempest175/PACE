import { useState, useEffect } from 'react'
import { HashRouter, Routes, Route, Link } from 'react-router-dom'
import { ThemeProvider } from './ThemeContext'
import { Sidebar } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { QuickActions } from './components/QuickActions'
import { WorkspaceCard } from './components/WorkspaceCard'
import { HardwareMonitor } from './components/HardwareMonitor'
import { ActivityTimeline } from './components/ActivityTimeline'
import { RecentChats } from './components/RecentChats'
import { SearchModal } from './components/SearchModal'
import { SettingsModal } from './components/SettingsModal'
import { ChatInterface } from './components/ChatInterface'
import { Cpu, Zap, ArrowRight, ShieldCheck } from 'lucide-react'

const API_BASE = '/api'

const masteryCards = [
  {
    icon: 'code',
    title: 'Coding Mastery',
    slug: 'coding',
    tag: 'Python & JS/TS',
    actor: 'Actor generates optimized code logic & async handlers.',
    critic: 'Critic executes static analysis & AST loop detection.',
    badge: 'Dual-Engine Active',
  },
  {
    icon: 'book',
    title: 'Literacy Mastery',
    slug: 'literacy',
    tag: 'NLP & Summarization',
    actor: 'Actor synthesizes multi-page technical documentation.',
    critic: 'Critic verifies factual consistency & NLI mapping.',
    badge: 'NLI Verified',
  },
  {
    icon: 'globe',
    title: 'Research Mastery',
    slug: 'research',
    tag: 'Academic Synthesis',
    actor: 'Actor compiles live literature & paper abstracts.',
    critic: 'Critic audits citations & cross-checks sources.',
    badge: 'Live Citations',
  },
]

function DashboardHome() {
  return (
    <div className="dashboard-view">
      {/* Enterprise Hero Banner (Solid Dark Flat Surface - NO Gradients) */}
      <section className="hero-banner-card">
        <div className="hero-text-content">
          <div className="hero-eyebrow">
            <Cpu size={14} />
            <span>Pipelined Actor-Critic Ensemble Architecture</span>
          </div>
          <h1 className="hero-title">PACE AI Platform</h1>
          <p className="hero-description">
            High-performance dual-model workspace running entirely locally on 8GB VRAM with zero data leakage.
            Powered by dynamic Actor generation and Critic NLI validation.
          </p>
        </div>

        <div className="hero-stats-group">
          <div className="stat-pill-box">
            <span className="stat-pill-value">8.0 GB</span>
            <span className="stat-pill-label">VRAM Ceiling</span>
          </div>
          <div className="stat-pill-box">
            <span className="stat-pill-value">~120 ms</span>
            <span className="stat-pill-label">Local Latency</span>
          </div>
        </div>
      </section>

      {/* Quick Actions Starter Workflows */}
      <QuickActions />

      {/* Interactive Mastery Workspaces Grid */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="section-label-heading">
          <Zap size={18} style={{ color: 'var(--accent-primary)' }} />
          <span>Select Mastery Workspace</span>
        </div>
        <div className="workspace-cards-grid">
          {masteryCards.map((card) => (
            <WorkspaceCard key={card.slug} card={card} />
          ))}
        </div>
      </section>

      {/* Hardware Telemetry Monitor & Activity Feed */}
      <div className="dashboard-grid-split">
        <HardwareMonitor />
        <ActivityTimeline />
      </div>

      {/* Recent Chat Sessions */}
      <RecentChats />
    </div>
  )
}

function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    const checkHealth = () => {
      fetch(`${API_BASE}/health`)
        .then((r) => r.json())
        .then((d) => setBackendStatus(d.status === 'healthy' ? 'connected' : 'error'))
        .catch(() => setBackendStatus('error'))
    }

    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  // Custom event listener to open search modal
  useEffect(() => {
    const handleOpenSearch = () => setIsSearchOpen(true)
    window.addEventListener('pace-open-search', handleOpenSearch)
    return () => window.removeEventListener('pace-open-search', handleOpenSearch)
  }, [])

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Content Area */}
      <div className="main-content" style={{ paddingLeft: collapsed ? '72px' : '260px' }}>
        <TopNav
          onOpenSearch={() => setIsSearchOpen(true)}
          onOpenSettings={() => setIsSettingsOpen(true)}
          setMobileOpen={setMobileOpen}
          backendStatus={backendStatus}
        />

        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="/coding" element={<ChatInterface type="coding" />} />
          <Route path="/literacy" element={<ChatInterface type="literacy" />} />
          <Route path="/research" element={<ChatInterface type="research" />} />
        </Routes>
      </div>

      {/* Command Palette Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Preferences Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <HashRouter>
        <MainLayout />
      </HashRouter>
    </ThemeProvider>
  )
}
