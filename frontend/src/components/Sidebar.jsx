import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Plus,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Settings,
  HardDrive,
  MessageSquare,
  Trash2,
  Code2,
  BookOpen,
  Globe2
} from 'lucide-react'

export function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen, onOpenSettings }) {
  const location = useLocation()
  const navigate = useNavigate()

  // ChatGPT-style Chat History list (Today's conversations only)
  const [chatHistory, setChatHistory] = useState([
    {
      id: 'chat-1',
      title: 'Async Retry Handler with Backoff',
      workspace: 'coding',
      group: 'Today',
      icon: Code2,
    },
    {
      id: 'chat-2',
      title: 'Custom React Debounce Hook',
      workspace: 'coding',
      group: 'Today',
      icon: Code2,
    },
  ])

  const [activeChatId, setActiveChatId] = useState('chat-1')

  const handleNewChat = () => {
    window.dispatchEvent(new CustomEvent('pace-new-chat'))
    if (location.pathname === '/') {
      navigate('/coding')
    }
  }

  const handleDeleteChat = (e, id) => {
    e.stopPropagation()
    e.preventDefault()
    setChatHistory((prev) => prev.filter((chat) => chat.id !== id))
  }

  const handleSelectChat = (chat) => {
    setActiveChatId(chat.id)
    setMobileOpen(false)
    navigate(`/${chat.workspace}`)
  }

  // Group history items by time group (Today only)
  const groups = ['Today']

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

          {groups.map((groupName) => {
            const itemsInGroup = chatHistory.filter((c) => c.group === groupName)
            if (itemsInGroup.length === 0) return null

            return (
              <div key={groupName} className="nav-group" style={{ marginTop: '12px' }}>
                {!collapsed && <div className="nav-group-title">{groupName}</div>}
                {itemsInGroup.map((chat) => {
                  const Icon = chat.icon || MessageSquare
                  const isActive = activeChatId === chat.id && location.pathname === `/${chat.workspace}`
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
                  );
                })}
              </div>
            )
          })}
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
                <div className="vram-bar-fill" style={{ width: '42%' }} />
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
