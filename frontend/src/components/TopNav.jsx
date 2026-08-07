import { useState, useEffect } from 'react'
import { Search, Menu, Zap, Shield, Bell, User, Settings } from 'lucide-react'

export function TopNav({ onOpenSearch, onOpenSettings, setMobileOpen, backendStatus }) {
  const [showProfileMenu, setShowProfileMenu] = useState(false)

  return (
    <header className="topnav-root">
      <div className="topnav-left">
        <button
          className="mobile-drawer-btn"
          onClick={() => setMobileOpen((prev) => !prev)}
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <button className="search-trigger-btn" onClick={onOpenSearch} title="Search workspace (Ctrl+K)">
          <Search size={16} />
          <span>Search or type command...</span>
          <span className="kbd-badge">Ctrl K</span>
        </button>
      </div>

      <div className="topnav-right">
        {/* Backend Health Status Pill */}
        <div className="status-pill">
          <span className={`status-indicator-dot ${backendStatus === 'connected' ? 'online' : backendStatus === 'checking' ? 'checking' : 'offline'}`} />
          <span>
            {backendStatus === 'connected'
              ? 'System Online'
              : backendStatus === 'checking'
              ? 'Connecting...'
              : 'Backend Offline'}
          </span>
        </div>

        {/* Notifications Icon Button */}
        <button className="icon-action-btn" title="Notifications">
          <Bell size={18} />
        </button>

        {/* Settings Icon Button */}
        <button className="icon-action-btn" onClick={onOpenSettings} title="Settings">
          <Settings size={18} />
        </button>

        {/* User Profile Avatar */}
        <div style={{ position: 'relative' }}>
          <button
            className="profile-avatar-btn"
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            title="User Profile"
          >
            AI
          </button>

          {showProfileMenu && (
            <div
              style={{
                position: 'absolute',
                top: '48px',
                right: '0',
                width: '200px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '8px',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 100,
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-subtle)' }}>
                <strong style={{ fontSize: '13px', color: 'var(--text-primary)', display: 'block' }}>Local Engineer</strong>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>8GB VRAM Workspace</span>
              </div>
              <button
                className="nav-item-link"
                style={{ width: '100%', border: 'none', background: 'transparent', cursor: 'pointer' }}
                onClick={() => {
                  setShowProfileMenu(false)
                  onOpenSettings()
                }}
              >
                <Settings size={15} />
                <span>Preferences</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
