import { useState, useEffect, useRef, useMemo } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Zap,
  Shield,
  Trash2,
  Copy,
  Check,
  Cpu,
  Sparkles,
  Loader2,
  Code2,
  BookOpen,
  Globe2,
  Layers,
  Paperclip,
  AlertTriangle,
} from 'lucide-react'
import { telemetryStore } from '../utils/telemetryStore'
import { ThinkingIndicator } from './ThinkingIndicator'

const API_BASE = '/api'

const modesConfig = {
  coding: {
    title: 'Coding Mastery',
    badge: 'Python / JS Engine',
    placeholder: 'Ask PACE coding (e.g. write an algorithm, refactor code)...',
    welcome: 'Welcome to PACE Coding Mastery. I am ready to process your requests locally. How can I help you today?',
    suggestions: [
      { title: 'Async Retry Handler', desc: 'Write a Python async wrapper with exponential backoff & jitter', icon: Code2 },
      { title: 'Custom React Hook', desc: 'Build a hook for debounced search with local storage cache', icon: Zap },
      { title: 'SQL Query Optimization', desc: 'Refactor complex JOIN query for 10M+ row dataset', icon: Layers },
    ],
  },
  literacy: {
    title: 'Literacy Mastery',
    badge: 'NLI Logic Engine',
    placeholder: 'Ask PACE literacy (e.g. summarize text, clarify concepts)...',
    welcome: 'Welcome to PACE Literacy Mastery. I am ready to process your requests locally. How can I help you today?',
    suggestions: [
      { title: 'Architecture Summary', desc: 'Extract key trade-offs from a technical design document', icon: BookOpen },
      { title: 'Executive Brief', desc: 'Draft a concise executive summary for system reliability', icon: Sparkles },
      { title: 'Spec Refinement', desc: 'Improve tone and structure of an engineering RFC proposal', icon: Layers },
    ],
  },
  research: {
    title: 'Research Mastery',
    badge: 'Citation Auditor',
    placeholder: 'Ask PACE research (e.g. compare architectures, summarize papers)...',
    welcome: 'Welcome to PACE Research Mastery. I am ready to process your requests locally. How can I help you today?',
    suggestions: [
      { title: 'Transformer vs Mamba', desc: 'Compare state-space models vs self-attention memory efficiency', icon: Globe2 },
      { title: 'KV Cache Compression', desc: 'Synthesize recent state-of-the-art LLM quantization methods', icon: Cpu },
      { title: '4-bit vs 8-bit Benchmarks', desc: 'Analyze perplexity trade-offs between GGUF and AWQ formats', icon: Cpu },
    ],
  },
}

export function ChatInterface({ type }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const activeChatId = searchParams.get('chat')

  const mode = modesConfig[type] || modesConfig.coding

  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState(null)
  const [speedMode, setSpeedMode] = useState('pro') // 'pro' | 'fast'
  const [copiedIndex, setCopiedIndex] = useState(null)

  const activeChatIdRef = useRef(activeChatId)
  const abortControllerRef = useRef(null)
  const messagesEndRef = useRef(null)

  const renderedWelcome = useMemo(() => mode.welcome.replaceAll('**', ''), [mode.welcome])

  useEffect(() => {
    activeChatIdRef.current = activeChatId
  }, [activeChatId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Fetch conversation messages on activeChatId change with AbortController for race condition protection
  useEffect(() => {
    if (!activeChatId) {
      setMessages([])
      setHistoryLoading(false)
      setHistoryError(null)
      return
    }

    // Cancel previous inflight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const controller = new AbortController()
    abortControllerRef.current = controller

    const loadConversation = async () => {
      setHistoryLoading(true)
      setHistoryError(null)
      setMessages([]) // Don't temporarily show messages from previous conversation

      try {
        const res = await fetch(`${API_BASE}/conversations/${activeChatId}`, {
          signal: controller.signal,
        })

        if (!res.ok) {
          throw new Error(`Failed to load chat (${res.status})`)
        }

        const data = await res.json()

        // Rapid clicking check: verify active chat ID hasn't changed while request was in-flight
        if (activeChatIdRef.current === activeChatId) {
          setMessages(data.messages || [])
        }
      } catch (err) {
        if (err.name === 'AbortError') return
        if (activeChatIdRef.current === activeChatId) {
          setHistoryError(err.message || 'Error loading conversation messages.')
        }
      } finally {
        if (activeChatIdRef.current === activeChatId) {
          setHistoryLoading(false)
        }
      }
    }

    loadConversation()

    return () => {
      controller.abort()
    }
  }, [activeChatId])

  // Listen for global custom event 'pace-new-chat'
  useEffect(() => {
    const handleReset = () => {
      setMessages([])
      setInput('')
      setHistoryError(null)
    }
    window.addEventListener('pace-new-chat', handleReset)
    return () => window.removeEventListener('pace-new-chat', handleReset)
  }, [])

  // Check if an initial prompt was passed via navigation state
  useEffect(() => {
    if (location.state?.initialPrompt) {
      submitWithText(location.state.initialPrompt)
    }
  }, [location.state])

  useEffect(() => {
    if (copiedIndex !== null) {
      const timer = setTimeout(() => setCopiedIndex(null), 2000)
      return () => clearTimeout(timer)
    }
  }, [copiedIndex])

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index)
    }).catch(() => {})
  }

  const handleNewChat = () => {
    window.dispatchEvent(new CustomEvent('pace-new-chat'))
    navigate(`/${type}`)
  }

  const submitWithText = async (textToSubmit) => {
    const value = textToSubmit.trim()
    if (!value || loading) return

    const messageId = Date.now().toString()
    let currentConversationId = activeChatId

    setMessages((prev) => [...prev, { id: messageId, role: 'user', text: value }])
    setInput('')
    setLoading(true)

    // Add assistant message streaming placeholder
    const assistantMsgId = (Date.now() + 1).toString()
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        text: '',
        status: 'Starting pipeline...',
        source: 'actor-critic-ensemble',
      },
    ])

    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: value,
          mode: type,
          speed_mode: speedMode,
          conversation_id: currentConversationId,
        }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let done = false
      let buffer = ''

      while (!done) {
        const { value: chunk, done: doneReading } = await reader.read()
        done = doneReading

        if (chunk) {
          buffer += decoder.decode(chunk, { stream: true })
          const lines = buffer.split('\n\n')
          buffer = lines.pop() // keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6)
              try {
                const data = JSON.parse(dataStr)

                if (data.type === 'init') {
                  if (data.conversation_id && data.conversation_id !== currentConversationId) {
                    currentConversationId = data.conversation_id
                    // Update URL without full page reload
                    navigate(`/${type}?chat=${currentConversationId}`, { replace: true })
                    // Refresh sidebar
                    window.dispatchEvent(new CustomEvent('pace-refresh-chats'))
                  }
                } else if (data.type === 'telemetry') {
                  // Emit real telemetry update to global monitor
                  telemetryStore.emit(data.metrics)
                } else if (data.type === 'status') {
                  setMessages((prev) =>
                    prev.map(msg => msg.id === assistantMsgId
                      ? { ...msg, status: data.content }
                      : msg
                    )
                  )
                } else if (data.type === 'clear') {
                  setMessages((prev) =>
                    prev.map(msg => msg.id === assistantMsgId
                      ? { ...msg, text: '' }
                      : msg
                    )
                  )
                } else if (data.type === 'token') {
                  setMessages((prev) =>
                    prev.map(msg => msg.id === assistantMsgId
                      ? { ...msg, text: msg.text + data.content }
                      : msg
                    )
                  )
                } else if (data.type === 'error') {
                  setMessages((prev) =>
                    prev.map(msg => msg.id === assistantMsgId
                      ? { ...msg, text: data.content, source: 'error', status: 'Error' }
                      : msg
                    )
                  )
                } else if (data.type === 'done') {
                  setMessages((prev) =>
                    prev.map(msg => msg.id === assistantMsgId
                      ? { ...msg, status: 'Critic Validated' }
                      : msg
                    )
                  )
                  window.dispatchEvent(new CustomEvent('pace-refresh-chats'))
                }
              } catch (e) {
                console.error("Error parsing JSON:", e, "Data:", dataStr)
              }
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map(msg => msg.id === assistantMsgId
          ? { ...msg, text: `⚠️ Could not reach local backend.\n\n(${err.message})`, source: 'error', status: 'Connection Failed' }
          : msg
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', text: `📎 Uploading document: ${file.name}` }])

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()

      if (data.status === 'error' || data.error) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: `⚠️ Upload Error: ${data.error || 'Failed to process document'}`,
            source: 'error',
          },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: `📄 **Document Ingested: ${data.filename}**\n\n- **Pages:** ${data.pages}\n- **Characters:** ${data.characters}\n- **Extracted Chunks:** ${data.chunks}\n\n**Preview Chunk:**\n\`\`\`\n${data.preview || '(Empty preview)'}\n\`\`\``,
            source: 'actor-critic-ensemble',
          },
        ])
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `⚠️ Upload failed: ${err.message}`,
          source: 'error',
        },
      ])
    } finally {
      setLoading(false)
      event.target.value = ''
    }
  }

  const submit = (event) => {
    event.preventDefault()
    submitWithText(input)
  }

  return (
    <div className="chat-workspace-root">
      {/* Header Bar */}
      <div className="chat-header-bar">
        <div className="chat-header-title-group">
          <h1 className="chat-title">{mode.title}</h1>
          <span className="mastery-tag-pill">{mode.badge}</span>
        </div>

        {/* Speed Switcher */}
        <div className="speed-switch-group">
          <button
            className={`speed-option-btn ${speedMode === 'fast' ? 'active' : ''}`}
            onClick={() => setSpeedMode('fast')}
            type="button"
          >
            <Zap size={14} />
            <span>Fast (8B)</span>
          </button>
          <button
            className={`speed-option-btn ${speedMode === 'pro' ? 'active' : ''}`}
            onClick={() => setSpeedMode('pro')}
            type="button"
          >
            <Shield size={14} />
            <span>Pro Ensemble</span>
          </button>
        </div>

        {activeChatId && (
          <button
            className="icon-action-btn"
            onClick={handleNewChat}
            title="Start New Session"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages-container">
        {/* Welcome Message */}
        <div className="msg-row">
          <div className="assistant-msg-box">
            <div className="assistant-avatar-box">
              <Cpu size={18} />
            </div>
            <div className="assistant-content-wrap">
              <p className="assistant-text-content">{renderedWelcome}</p>
              <div className="assistant-meta-bar">
                <span className="critic-validated-badge">
                  <Check size={13} /> Critic Validated
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Loading State for History */}
        {historyLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: '10px', color: 'var(--text-secondary)' }}>
            <Loader2 size={20} className="spin" style={{ animation: 'spin-shimmer 2s infinite linear' }} />
            <span>Loading conversation messages...</span>
          </div>
        )}

        {/* Error State for History */}
        {historyError && (
          <div className="msg-row">
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--status-red)', borderRadius: 'var(--radius-md)', padding: '16px', color: '#EF4444', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AlertTriangle size={18} />
              <span>{historyError}</span>
            </div>
          </div>
        )}

        {/* Messages Stream */}
        {!historyLoading && messages.map((msg, index) => {
          const isLastAssistantMsg = loading && index === messages.length - 1 && msg.role === 'assistant'
          const isThinking = isLastAssistantMsg && (!msg.text || msg.text === '')

          return msg.role === 'user' ? (
            <div className="msg-row user" key={msg.id || `msg-${index}`}>
              <div className="user-bubble">{msg.text}</div>
            </div>
          ) : (
            <div className="msg-row" key={msg.id || `msg-${index}`}>
              <div className="assistant-msg-box">
                <div className={`assistant-avatar-box ${isThinking ? 'thinking' : ''}`}>
                  <Cpu size={18} />
                </div>
                <div className="assistant-content-wrap">
                  {isThinking ? (
                    <ThinkingIndicator status={msg.status || 'AI is thinking'} />
                  ) : (
                    <div className="assistant-text-content" style={{ fontFamily: 'var(--font-sans)', lineHeight: '1.6' }}>
                      {(() => {
                        if (!msg.text) return null;
                        // Split by ```lang ... ```
                        const parts = msg.text.split(/```(\w*)\n([\s\S]*?)```/g);
                        return parts.map((part, i) => {
                          if (i % 3 === 2) {
                            // Code block content
                            return (
                              <div key={i} style={{ margin: '12px 0', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                                <div style={{ backgroundColor: 'var(--bg-card-hover)', padding: '6px 12px', fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', borderBottom: '1px solid var(--border-subtle)' }}>
                                  {parts[i-1] || 'code'}
                                </div>
                                <pre style={{ margin: 0, padding: '12px', overflowX: 'auto', backgroundColor: 'var(--bg-canvas)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
                                  {part}
                                </pre>
                              </div>
                            );
                          } else if (i % 3 === 0) {
                            // Normal text
                            return <span key={i} style={{ whiteSpace: 'pre-wrap' }}>{part}</span>;
                          }
                          return null;
                        });
                      })()}
                    </div>
                  )}
                  <div className="assistant-meta-bar">
                    <span className="critic-validated-badge">
                      {isThinking ? (
                        <Sparkles size={13} style={{ color: 'var(--accent-primary)', animation: 'spark-pulse 1.8s infinite' }} />
                      ) : (
                        <Check size={13} />
                      )}
                      {msg.source === 'actor-critic-ensemble'
                        ? (msg.status || 'Critic Validated')
                        : msg.source === 'error'
                        ? 'Connection Error'
                        : 'Fallback Mode'}
                    </span>
                    {!isThinking && (
                      <button
                        className="copy-text-btn"
                        onClick={() => copyToClipboard(msg.text, index)}
                        title="Copy response"
                      >
                        {copiedIndex === index ? <Check size={13} /> : <Copy size={13} />}
                        <span>{copiedIndex === index ? 'Copied' : 'Copy'}</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        <div ref={messagesEndRef} />

        {/* Prompt Suggestions (Empty State) */}
        {!historyLoading && messages.length === 0 && mode.suggestions && (
          <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Recommended Workflow Starters
            </div>
            <div className="quick-actions-grid">
              {mode.suggestions.map((sug, idx) => {
                const Icon = sug.icon
                return (
                  <div
                    key={idx}
                    className="quick-action-card"
                    onClick={() => submitWithText(sug.desc)}
                  >
                    <div className="action-card-top">
                      <div className="action-icon-wrapper">
                        <Icon size={18} />
                      </div>
                    </div>
                    <strong className="action-title">{sug.title}</strong>
                    <p className="action-desc">{sug.desc}</p>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Floating Composer */}
      <div className="composer-container">
        <form className="composer-form" onSubmit={submit}>
          <label
            title="Upload PDF document to backend"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              cursor: loading ? 'not-allowed' : 'pointer',
              color: 'var(--text-secondary)',
              transition: 'var(--transition-fast)',
            }}
          >
            <Paperclip size={18} />
            <input
              type="file"
              accept=".pdf"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={loading}
            />
          </label>
          <input
            className="composer-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={mode.placeholder}
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                if (!loading && input.trim()) {
                  submitWithText(input)
                }
              }
            }}
          />
          <button
            type="submit"
            className="send-msg-btn"
            disabled={loading || !input.trim()}
            title="Send query"
          >
            <Send size={16} />
          </button>
        </form>
        <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
          PACE Dual-Engine running locally on 8GB VRAM • Critic NLI Audit Enabled
        </div>
      </div>
    </div>
  )
}
