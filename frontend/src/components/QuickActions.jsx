import { useNavigate } from 'react-router-dom'
import { Code2, BookOpen, Globe2, Cpu, ArrowUpRight } from 'lucide-react'

export function QuickActions() {
  const navigate = useNavigate()

  const actions = [
    {
      title: 'Build Async Retry Handler',
      desc: 'Generate Python wrapper with exponential backoff & jitter',
      icon: Code2,
      path: '/coding',
      prompt: 'Write a Python async wrapper with exponential backoff & jitter for network retries.',
    },
    {
      title: 'Summarize Technical RFC',
      desc: 'Extract key design trade-offs and architectural impacts',
      icon: BookOpen,
      path: '/literacy',
      prompt: 'Extract key trade-offs and structural implications from a technical spec proposal.',
    },
    {
      title: 'KV Cache Compression',
      desc: 'Compare SOTA LLM quantization methods (AWQ vs GGUF)',
      icon: Globe2,
      path: '/research',
      prompt: 'Compare state-of-the-art KV cache compression & quantization methods for 8GB VRAM.',
    },
    {
      title: 'Benchmark System Latency',
      desc: 'Audit dual-engine Actor-Critic pipeline throughput',
      icon: Cpu,
      path: '/coding',
      prompt: 'Write a benchmark script measuring token generation latency and throughput.',
    },
  ]

  const handleActionClick = (action) => {
    navigate(action.path, { state: { initialPrompt: action.prompt } })
  }

  return (
    <section className="quick-actions-section">
      <div className="section-label-heading">
        <span>Quick Workflows</span>
      </div>

      <div className="quick-actions-grid">
        {actions.map((action, idx) => {
          const Icon = action.icon
          return (
            <div
              key={idx}
              className="quick-action-card"
              onClick={() => handleActionClick(action)}
            >
              <div className="action-card-top">
                <div className="action-icon-wrapper">
                  <Icon size={20} />
                </div>
                <ArrowUpRight size={16} style={{ color: 'var(--text-muted)' }} />
              </div>
              <span className="action-title">{action.title}</span>
              <p className="action-desc">{action.desc}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
