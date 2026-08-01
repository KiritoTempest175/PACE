import { useMemo, useState } from 'react'
import { HashRouter, Link, Route, Routes, useNavigate } from 'react-router-dom'
import { ThemeProvider, useTheme } from './ThemeContext'

const API_BASE = '/api'

const Icon = ({ name, size = 22 }) => {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  }

  const icons = {
    terminal: <svg {...common}><path d="m7 7 4 5-4 5"/><path d="M13 17h4"/></svg>,
    sun: <svg {...common}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"/></svg>,
    moon: <svg {...common}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>,
    code: <svg {...common}><path d="m8 9-3 3 3 3"/><path d="m16 9 3 3-3 3"/><path d="m14 5-4 14"/></svg>,
    book: <svg {...common}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"/></svg>,
    globe: <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></svg>,
    chip: <svg {...common}><rect x="7" y="7" width="10" height="10" rx="1"/><rect x="10" y="10" width="4" height="4"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg>,
    external: <svg {...common}><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>,
    arrowLeft: <svg {...common}><path d="m15 18-6-6 6-6"/></svg>,
    menu: <svg {...common}><path d="M4 6h16M4 12h16M4 18h16"/></svg>,
    close: <svg {...common}><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>,
    message: <svg {...common}><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>,
    settings: <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.12 2.12-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V20h-3v-.08A1.7 1.7 0 0 0 10.68 18.36a1.7 1.7 0 0 0-1.88.34l-.06.06-2.12-2.12.06-.06A1.7 1.7 0 0 0 7.02 15a1.7 1.7 0 0 0-1.56-1.03H5v-3h.46A1.7 1.7 0 0 0 7.02 9.94a1.7 1.7 0 0 0-.34-1.88L6.62 8l2.12-2.12.06.06a1.7 1.7 0 0 0 1.88.34A1.7 1.7 0 0 0 11.71 4.7V4h3v.7a1.7 1.7 0 0 0 1.03 1.58 1.7 1.7 0 0 0 1.88-.34l.06-.06L19.8 8l-.06.06a1.7 1.7 0 0 0-.34 1.88A1.7 1.7 0 0 0 20.96 11H21v3h-.04A1.7 1.7 0 0 0 19.4 15z"/></svg>,
    send: <svg {...common}><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>,
    check: <svg {...common}><path d="m5 12 4 4L19 6"/></svg>,
    bolt: <svg {...common}><path d="m13 2-9 12h7l-1 8 9-12h-7z"/></svg>,
    shield: <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>,
    loader: <svg {...common} className="spin-icon"><circle cx="12" cy="12" r="10" strokeDasharray="50" strokeDashoffset="15"/></svg>,
  }

  return icons[name] ?? null
}

const masteryCards = [
  { icon: 'code', title: 'Coding Mastery', slug: 'coding', actor: 'Generates optimized Python/JS logic.', critic: 'Validates syntax, catches infinite loops.' },
  { icon: 'book', title: 'Literacy Mastery', slug: 'literacy', actor: 'Summarizes and extracts key information.', critic: 'Checks factual consistency (NLI mapping).' },
  { icon: 'globe', title: 'Research Mastery', slug: 'research', actor: 'Synthesizes live academic sources.', critic: 'Verifies citation existence & accuracy.' },
]

const modes = {
  coding: { title: 'Coding Mastery', placeholder: 'Ask PACE coding...', welcome: 'Welcome to **PACE Coding Mastery**. I am ready to process your requests locally. How can I help you today?' },
  literacy: { title: 'Literacy Mastery', placeholder: 'Ask PACE literacy...', welcome: 'Welcome to **PACE Literacy Mastery**. I am ready to process your requests locally. How can I help you today?' },
  research: { title: 'Research Mastery', placeholder: 'Ask PACE research...', welcome: 'Welcome to **PACE Research Mastery**. I am ready to process your requests locally. How can I help you today?' },
}

function ThemeToggle({ size = 20 }) {
  const { theme, toggleTheme } = useTheme()
  return (
    <button className="theme-btn" onClick={toggleTheme} aria-label="Toggle theme">
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={size} />
    </button>
  )
}

function StatusDot({ status }) {
  const color = status === 'connected' ? 'var(--accent-green)' : status === 'checking' ? 'orange' : '#ff4444'
  return <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: color, marginRight: 6 }} />
}

function HomePage() {
  const [backendStatus, setBackendStatus] = useState('checking')

  useState(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then((d) => setBackendStatus(d.status === 'healthy' ? 'connected' : 'error'))
      .catch(() => setBackendStatus('error'))
  })

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="PACE home">
          <span className="brand-mark"><Icon name="terminal" size={20} /></span>
          <span>PACE</span>
        </a>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)', display: 'flex', alignItems: 'center' }}>
            <StatusDot status={backendStatus} />
            {backendStatus === 'connected' ? 'Backend online' : backendStatus === 'checking' ? 'Connecting…' : 'Backend offline'}
          </span>
          <ThemeToggle />
        </div>
      </header>

      <main id="top">
        <section className="hero section-wrap">
          <div className="eyebrow"><span className="eyebrow-dot"/>Pipelined Actor-Critic Ensemble</div>
          <h1>PACE Engine</h1>
          <p className="hero-copy">A highly optimized, dual-model AI ecosystem running entirely locally on<br className="desktop-break" />8GB VRAM. Flawless execution through dynamic Actor-Critic model<br className="desktop-break" />swapping.</p>

          <div className="watchdog-card">
            <div className="watchdog-head">
              <div className="watchdog-title"><Icon name="chip" size={18}/> <span>VRAM Watchdog</span></div>
              <span className="max-badge">MAX 8.0 GB</span>
            </div>
            <div className="usage-row"><strong>Idle state</strong><span>8 MB</span></div>
            <div className="progress-track"><div className="progress-fill" /></div>
            <div className="scale"><span>0 GB</span><span>4 GB</span><span>8 GB</span></div>
          </div>
        </section>

        <section className="mastery section-wrap">
          <h2>Select Mastery</h2>
          <div className="card-grid">
            {masteryCards.map((card) => (
              <Link className="mastery-card" to={`/${card.slug}`} key={card.title} aria-label={`Open ${card.title}`}>
                <div className="icon-box"><Icon name={card.icon} size={28} /></div>
                <h3>{card.title}</h3>
                <p><strong>Actor:</strong> {card.actor}</p>
                <p><strong>Critic:</strong> {card.critic}</p>
                <span className="open-label">Open workspace →</span>
              </Link>
            ))}
          </div>
        </section>
      </main>

      <footer>
        <div className="footer-inner section-wrap">
          <nav className="footer-links" aria-label="Primary footer links">
            <a href="#docs"><Icon name="book" size={16}/>Docs</a>
            <a href="#github"><Icon name="code" size={16}/>GitHub</a>
            <a href="#paper"><Icon name="external" size={15}/>Paper</a>
          </nav>
          <div className="footer-meta"><span>Created by</span><a href="#portfolio">Portfolio</a><span className="dot">•</span><a href="#team">Team</a></div>
        </div>
      </footer>
    </div>
  )
}

function MasteryPage({ type }) {
  const navigate = useNavigate()
  const mode = modes[type]
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const renderedWelcome = useMemo(() => mode.welcome.replaceAll('**', ''), [mode.welcome])

  const submit = async (event) => {
    event.preventDefault()
    const value = input.trim()
    if (!value || loading) return

    // Add user message
    setMessages((prev) => [...prev, { role: 'user', text: value }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: value }),
      })
      const data = await res.json()
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.response,
          source: data.source || 'unknown',
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `⚠️ Could not reach backend.\n\nMake sure the FastAPI server is running on port 8000.\n\n(${err.message})`,
          source: 'error',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="workspace-shell">
      {/* Mobile sidebar overlay */}
      <div
        className={`sidebar-overlay${sidebarOpen ? ' sidebar-open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar${sidebarOpen ? ' sidebar-open' : ''}`}>
        <button className="sidebar-close" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
          <Icon name="close" size={18} />
        </button>
        <button className="sidebar-brand" onClick={() => navigate('/')}>
          <span className="back-box"><Icon name="arrowLeft" size={20}/></span>
          <span>PACE Engine</span>
        </button>
        <div className="history">
          <p>SESSION HISTORY</p>
          <div className="current-session"><Icon name="message" size={17}/><span>Current Session</span></div>
        </div>
        <button className="settings-row"><Icon name="settings" size={18}/><span>Settings</span></button>
      </aside>

      <section className="workspace-main">
        <header className="workspace-header">
          <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <Icon name="menu" size={20} />
          </button>
          <h1>{mode.title}</h1>
          <div className="speed-switch"><span><Icon name="bolt" size={15}/> Fast</span><span className="active"><Icon name="shield" size={15}/> Pro</span></div>
          <ThemeToggle size={19} />
        </header>

        <div className="conversation">
          <div className="assistant-message">
            <div className="assistant-avatar"><Icon name="chip" size={19}/></div>
            <div>
              <p>{renderedWelcome}</p>
              <span className="validated"><Icon name="check" size={13}/> Critic Validated</span>
            </div>
          </div>

          {messages.map((msg, index) =>
            msg.role === 'user' ? (
              <div className="user-message" key={`msg-${index}`}>{msg.text}</div>
            ) : (
              <div className="assistant-message" key={`msg-${index}`}>
                <div className="assistant-avatar"><Icon name="chip" size={19}/></div>
                <div>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 14, lineHeight: 1.55, fontWeight: 600 }}>{msg.text}</pre>
                  <span className="validated">
                    <Icon name="check" size={13}/>
                    {msg.source === 'actor-critic-ensemble' ? 'Critic Validated' : msg.source === 'error' ? 'Connection Error' : 'Fallback Mode'}
                  </span>
                </div>
              </div>
            )
          )}

          {loading && (
            <div className="assistant-message">
              <div className="assistant-avatar"><Icon name="chip" size={19}/></div>
              <div>
                <p style={{ color: 'var(--text-dim)' }}>
                  <Icon name="loader" size={14} /> Processing through Actor-Critic pipeline…
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={submit}>
            <input value={input} onChange={(event) => setInput(event.target.value)} placeholder={mode.placeholder} aria-label={mode.placeholder} disabled={loading}/>
            <button type="submit" aria-label="Send message" disabled={loading}><Icon name="send" size={20}/></button>
          </form>
          <p>PACE Engine running locally. Verify critical outputs.</p>
        </div>
      </section>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/coding" element={<MasteryPage type="coding" />} />
          <Route path="/literacy" element={<MasteryPage type="literacy" />} />
          <Route path="/research" element={<MasteryPage type="research" />} />
        </Routes>
      </HashRouter>
    </ThemeProvider>
  )
}

export default App
