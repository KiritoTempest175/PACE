import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  LayoutDashboard,
  Plus,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Settings,
  MessageSquare,
  Trash2,
  Code2,
  BookOpen,
  Globe2
} from 'lucide-react'
import { telemetryStore } from '../utils/telemetryStore'

const API_BASE = '/api'

export function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen, onOpenSettings }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const activeChatIdFromUrl = searchParams.get('chat')

  const [chatHistory, setChatHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [vramPercent, setVramPercent] = useState(0)

  useEffect(() => {
    let isMounted = true
    const fetchVram = async () => {
      try {
        const res = await fetch(`${API_BASE}/telemetry`)
        if (res.ok && isMounted) {
          const data = await res.json()
          setVramPercent(data.vram_percent || 0)
        }
      } catch (e) {
        // ignore
      }
    }

    fetchVram()
    const interval = setInterval(fetchVram, 3000)

    const unsubscribe = telemetryStore.subscribe((data) => {
      if (data && data.vram_percent != null) {
        setVramPercent(data.vram_percent)
      }
    })

    return () => {
      isMounted = false
      clearInterval(interval)
      unsubscribe()
    }
  }, [])

  // Fetch real conversation history from SQLite database backend
  const fetchConversations = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/conversations`)
      if (res.ok) {
        const data = await res.json()
        setChatHistory(data)
      }
    } catch (e) {
      console.error("Failed to load conversations:", e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  // Listen for global chat creation/update events to refresh list
  useEffect(() => {
    const handleChatRefresh = () => fetchConversations()
    window.addEventListener('pace-refresh-chats', handleChatRefresh)
    return () => window.removeEventListener('pace-refresh-chats', handleChatRefresh)
  }, [fetchConversations])

  const handleNewChat = () => {
    window.dispatchEvent(new CustomEvent('pace-new-chat'))
    const currentWorkspace = location.pathname.startsWith('/literacy')
      ? 'literacy'
      : location.pathname.startsWith('/research')
      ? 'research'
      : 'coding'
    navigate(`/${currentWorkspace}`)
  }

  const handleDeleteChat = async (e, id) => {
    e.stopPropagation()
    e.preventDefault()

    try {
      await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' })
      setChatHistory((prev) => prev.filter((chat) => chat.id !== id))
      if (activeChatIdFromUrl === id) {
        handleNewChat()
      }
    } catch (err) {
      console.error("Failed to delete chat:", err)
    }
  }

  const handleSelectChat = (chat) => {
    setMobileOpen(false)
    const targetWorkspace = chat.workspace || 'coding'
    navigate(`/${targetWorkspace}?chat=${chat.id}`)
  }

  const getWorkspaceIcon = (ws) => {
    if (ws === 'literacy') return BookOpen
    if (ws === 'research') return Globe2
    return Code2
  }

  return (
    <>
      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-backdrop-overlay"
            style={{ paddingTop: 0, zIndex: 95 }}
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar-root ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        {/* Header Branding */}
        <div className="sidebar-header">
          <Link to="/" className="brand-logo-wrap">
            <div className="brand-icon-box">
              <Cpu size={20} />
            </div>
            {!collapsed && (
              <div className="brand-title-group">
                <span className="brand-title">PACE AI</span>
                <span className="brand-subtitle">v1.0 Ensemble</span>
              </div>
            )}
          </Link>

          <button
            className="sidebar-toggle-btn"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            aria-label="Toggle Sidebar"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Action Button: + New Chat */}
        <div className="sidebar-action-wrap">
          <button className="btn-new-chat" onClick={handleNewChat} title="Start new session">
            <Plus size={18} />
            {!collapsed && <span>New Chat</span>}
          </button>
        </div>

        {/* ChatGPT-style History Section */}
        <nav className="sidebar-nav-section">
          {/* Link to Home Dashboard */}
          <Link
            to="/"
            className={`nav-item-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => setMobileOpen(false)}
            title="Dashboard Overview"
          >
            <LayoutDashboard size={18} />
            {!collapsed && <span>Dashboard Overview</span>}
          </Link>

          <div className="nav-group" style={{ marginTop: '12px' }}>
            {!collapsed && <div className="nav-group-title">History</div>}

            {chatHistory.length === 0 && !loading && !collapsed && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '8px 12px' }}>
                No past sessions
              </div>
            )}

            {chatHistory.map((chat) => {
              const Icon = getWorkspaceIcon(chat.workspace)
              const isActive = activeChatIdFromUrl === chat.id
              return (
                <div
                  key={chat.id}
                  className={`nav-item-link ${isActive ? 'active' : ''}`}
                  onClick={() => handleSelectChat(chat)}
                  title={`${chat.title} (${chat.workspace})`}
                  style={{ cursor: 'pointer', position: 'relative' }}
                >
                  <Icon size={16} style={{ flexShrink: 0 }} />
                  {!collapsed && (
                    <span
                      style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        flex: 1,
                        fontSize: '13px',
                      }}
                    >
                      {chat.title}
                    </span>
                  )}
                  {!collapsed && (
                    <button
                      className="chat-delete-btn"
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                      title="Delete chat"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '2px',
                        borderRadius: '4px',
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </nav>

        {/* Footer Spec & Settings */}
        <div className="sidebar-footer">
          {!collapsed && (
            <div className="vram-spec-card">
              <div className="vram-spec-header">
                <span>VRAM Memory</span>
                <span>8.0 GB Max</span>
              </div>
              <div className="vram-bar-track">
                <div className="vram-bar-fill" style={{ width: `${vramPercent}%` }} />
              </div>
            </div>
          )}

          <button
            className="nav-item-link"
            style={{ width: '100%', background: 'transparent', border: 'none', cursor: 'pointer' }}
            onClick={onOpenSettings}
            title="Settings"
          >
            <Settings size={18} />
            {!collapsed && <span>Settings</span>}
          </button>
        </div>
      </aside>
    </>
  )
}
