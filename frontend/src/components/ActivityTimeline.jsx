import { Activity, CheckCircle2, Cpu, Zap, ShieldCheck } from 'lucide-react'

export function ActivityTimeline() {
  const events = [
    {
      id: 1,
      title: 'Critic NLI Audit Passed',
      desc: 'DeepSeek Coder verified AST loop-safety & zero memory leaks',
      time: '12:44:02 PM',
      icon: ShieldCheck,
      color: 'var(--status-emerald)',
    },
    {
      id: 2,
      title: 'Actor Token Generation',
      desc: 'Llama-3.1 8B completed inference stream (48.2 tok/s)',
      time: '12:44:00 PM',
      icon: Zap,
      color: 'var(--accent-primary)',
    },
    {
      id: 3,
      title: 'Hardware Cache Synced',
      desc: 'VRAM footprint re-allocated within 8GB limit (8.2 MB active)',
      time: '12:42:15 PM',
      icon: Cpu,
      color: 'var(--status-cyan)',
    },
    {
      id: 4,
      title: 'System Health Check',
      desc: 'Local FastAPI daemon responded in 1.4ms',
      time: '12:40:00 PM',
      icon: CheckCircle2,
      color: 'var(--status-emerald)',
    },
  ]

  return (
    <div className="activity-timeline-card" id="activity">
      <div className="section-label-heading">
        <Activity size={18} style={{ color: 'var(--accent-primary)' }} />
        <span>Execution Audit Feed</span>
      </div>

      <div className="timeline-feed-list">
        {events.map((evt) => {
          const Icon = evt.icon
          return (
            <div key={evt.id} className="timeline-item-row">
              <div className="timeline-icon-node" style={{ color: evt.color }}>
                <Icon size={14} />
              </div>
              <div className="timeline-content-body">
                <span className="timeline-event-title">{evt.title}</span>
                <span className="timeline-event-desc">{evt.desc}</span>
                <span className="timeline-time-stamp">{evt.time}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
