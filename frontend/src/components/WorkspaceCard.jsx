import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, Code2, BookOpen, Globe2 } from 'lucide-react'

export function WorkspaceCard({ card }) {
  const iconMap = {
    code: Code2,
    book: BookOpen,
    globe: Globe2,
  }

  const IconComponent = iconMap[card.icon] || Code2

  return (
    <Link to={`/${card.slug}`} className="mastery-card-root" aria-label={`Launch ${card.title}`}>
      <div className="mastery-card-top">
        <div className="mastery-icon-badge">
          <IconComponent size={24} />
        </div>
        <span className="mastery-tag-pill">{card.tag}</span>
      </div>

      <div className="mastery-card-body">
        <h3 className="mastery-card-title">{card.title}</h3>
        <div className="role-breakdown-box">
          <div className="role-row">
            <strong>Actor:</strong> {card.actor}
          </div>
          <div className="role-row">
            <strong>Critic:</strong> {card.critic}
          </div>
        </div>
      </div>

      <div className="mastery-card-footer">
        <span className="badge-engine">
          <CheckCircle2 size={14} />
          {card.badge}
        </span>
        <span className="launch-btn-link">
          Open Workspace <ArrowRight size={15} />
        </span>
      </div>
    </Link>
  )
}
