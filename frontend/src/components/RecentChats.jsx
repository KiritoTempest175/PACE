import { Link } from 'react-router-dom'
import { MessageSquare, ArrowRight, Code2, BookOpen, Globe2 } from 'lucide-react'

export function RecentChats() {
  const sessions = [
    {
      id: 'session-1',
      title: 'Async Retry Handler with Exponential Backoff',
      workspace: 'Coding Mastery',
      path: '/coding',
      icon: Code2,
      date: '10 mins ago',
    },
    {
      id: 'session-2',
      title: 'Technical Specification Executive Briefing',
      workspace: 'Literacy Mastery',
      path: '/literacy',
      icon: BookOpen,
      date: '2 hours ago',
    },
    {
      id: 'session-3',
      title: 'KV Cache Compression SOTA Comparison',
      workspace: 'Research Mastery',
      path: '/research',
      icon: Globe2,
      date: 'Yesterday',
    },
  ]

  return (
    <div className="recent-chats-card">
      <div className="section-label-heading">
        <MessageSquare size={18} style={{ color: 'var(--accent-primary)' }} />
        <span>Recent AI Workspaces & Sessions</span>
      </div>

      <div className="chats-list-grid">
        {sessions.map((sess) => {
          const Icon = sess.icon
          return (
            <Link key={sess.id} to={sess.path} className="chat-session-item">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--accent-soft)',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon size={18} />
                </div>
                <div className="session-info">
                  <span className="session-title">{sess.title}</span>
                  <span className="session-date">{sess.workspace} • {sess.date}</span>
                </div>
              </div>
              <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
