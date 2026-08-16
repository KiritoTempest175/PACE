import React from 'react'
import { Sparkles, Cpu } from 'lucide-react'

export function ThinkingIndicator({ status = 'AI is thinking' }) {
  return (
    <div className="thinking-indicator-wrapper">
      <div className="thinking-icon-badge">
        <Sparkles size={14} />
      </div>
      <span className="thinking-text">{status}</span>
      <div className="thinking-dots-container">
        <span className="thinking-dot" />
        <span className="thinking-dot" />
        <span className="thinking-dot" />
      </div>
    </div>
  )
}
