import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Cpu } from 'lucide-react'
import { telemetryStore } from '../utils/telemetryStore'

const API_BASE = '/api'

export function HardwareMonitor() {
  const [telemetry, setTelemetry] = useState({
    vram_allocated_mb: null,
    vram_total_mb: null,
    vram_percent: null,
    actor_model: 'PACE Actor 164M',
    critic_model: 'Qwen 2.5-3B',
    tokens_per_sec: null,
    latency_ms: null,
    device: 'CPU (Fallback)',
    status: 'idle',
    cpu_utilization: null,
    ram_usage_mb: null,
    gpu_utilization: null,
  })

  // Store real telemetry history points for SVG sparkline
  const [historyPoints, setHistoryPoints] = useState([])

  // Fetch real snapshot on mount
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const res = await fetch(`${API_BASE}/telemetry`)
        if (res.ok) {
          const data = await res.json()
          setTelemetry((prev) => ({ ...prev, ...data }))
          if (data.latency_ms != null) {
            setHistoryPoints((prev) => {
              const updated = [...prev, data.latency_ms]
              return updated.slice(-20)
            })
          }
        }
      } catch (e) {
        console.error('Failed to fetch initial telemetry:', e)
      }
    }

    fetchTelemetry()
  }, [])

  // Subscribe to real-time telemetry events from AI execution
  useEffect(() => {
    const unsubscribe = telemetryStore.subscribe((data) => {
      if (!data) return
      setTelemetry((prev) => ({ ...prev, ...data }))

      if (data.latency_ms != null && data.latency_ms > 0) {
        setHistoryPoints((prev) => {
          const updated = [...prev, data.latency_ms]
          return updated.slice(-20) // Keep last 20 real samples
        })
      }
    })

    return () => unsubscribe()
  }, [])

  // Generate dynamic SVG sparkline path strictly from REAL historical data points
  const buildSvgPath = () => {
    if (historyPoints.length < 2) {
      // Default flat baseline line if no historical requests recorded yet
      return {
        pathData: "M 0 70 L 400 70 L 400 100 L 0 100 Z",
        linePath: "M 0 70 L 400 70",
      }
    }

    const width = 400
    const height = 80
    const padding = 10

    const minVal = Math.min(...historyPoints)
    const maxVal = Math.max(...historyPoints)
    const range = maxVal === minVal ? 1 : maxVal - minVal

    const points = historyPoints.map((val, idx) => {
      const x = (idx / (historyPoints.length - 1)) * width
      const normalizedY = (val - minVal) / range
      const y = height - padding - normalizedY * (height - 2 * padding)
      return { x, y }
    })

    let linePath = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`
    for (let i = 1; i < points.length; i++) {
      linePath += ` L ${points[i].x.toFixed(1)} ${points[i].y.toFixed(1)}`
    }

    const pathData = `${linePath} L ${width} 100 L 0 100 Z`
    return { pathData, linePath }
  }

  const { pathData, linePath } = buildSvgPath()

  const isProcessing = telemetry.status === 'processing'
  const isHealthy = telemetry.status === 'completed' || telemetry.status === 'idle'

  return (
    <div className="hardware-monitor-card" id="hardware">
      <div className="monitor-header">
        <div className="monitor-title-group">
          <Cpu size={20} style={{ color: 'var(--accent-primary)' }} />
          <span>Hardware & VRAM Telemetry Monitor</span>
        </div>
        <span className="badge-vram-limit">
          {telemetry.vram_total_mb != null
            ? `MAX ${(telemetry.vram_total_mb / 1024).toFixed(1)} GB VRAM (${telemetry.device})`
            : `CAP 8.0 GB VRAM (${telemetry.device})`}
        </span>
      </div>

      <div className="hardware-metrics-grid">
        <div className="metric-tile">
          <span className="metric-tile-label">VRAM Allocated</span>
          <span className="metric-tile-value blue">
            {telemetry.vram_allocated_mb != null ? `${telemetry.vram_allocated_mb} MB` : 'N/A'}
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Actor Model</span>
          <span className="metric-tile-value emerald">
            {telemetry.actor_model || 'N/A'}
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Critic Model</span>
          <span className="metric-tile-value cyan">
            {telemetry.critic_model || 'N/A'}
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Local Throughput</span>
          <span className="metric-tile-value amber">
            {telemetry.tokens_per_sec != null ? `${telemetry.tokens_per_sec} tok/s` : 'N/A'}
          </span>
        </div>
      </div>

      {/* Dynamic SVG Telemetry Sparkline (Real Metrics Only) */}
      <div className="chart-container-box">
        <div className="chart-meta-row">
          <span>
            Real-time Latency Waveform (
            {telemetry.latency_ms != null ? `~${telemetry.latency_ms}ms` : 'N/A'}
            {telemetry.ttft_ms != null ? ` | TTFT: ${telemetry.ttft_ms}ms` : ''}
            )
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: isProcessing ? 'var(--accent-primary)' : 'var(--status-emerald)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isProcessing ? 'var(--accent-primary)' : 'var(--status-emerald)',
                boxShadow: isProcessing ? '0 0 8px var(--accent-primary)' : 'none',
              }}
            />
            {isProcessing ? 'Active Request Processing' : 'Idle (Last Run Telemetry)'}
          </span>
        </div>

        <div className="svg-chart-wrapper">
          <svg viewBox="0 0 400 100" preserveAspectRatio="none">
            {/* Background solid Area overlay */}
            <path d={pathData} fill="#16203D" opacity="0.4" />
            {/* Real Data Sparkline Path */}
            <motion.path
              d={linePath}
              fill="none"
              stroke={isProcessing ? "#4F7CFF" : "#10B981"}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              transition={{ duration: 0.2 }}
            />
          </svg>
        </div>
      </div>

      {/* VRAM / System Resource Progress Track */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <span>VRAM Footprint</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>
            {telemetry.vram_percent != null ? `${telemetry.vram_percent}% Utilized` : 'N/A'}
          </span>
        </div>
        <div className="vram-bar-track" style={{ height: '8px' }}>
          <div
            className="vram-bar-fill"
            style={{
              width: telemetry.vram_percent != null ? `${Math.max(0.1, telemetry.vram_percent)}%` : '0%',
            }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>0 GB</span>
          <span>
            {telemetry.ram_usage_mb != null
              ? `RAM: ${(telemetry.ram_usage_mb / 1024).toFixed(1)} GB`
              : '4 GB'}
          </span>
          <span>
            {telemetry.vram_total_mb != null
              ? `${(telemetry.vram_total_mb / 1024).toFixed(1)} GB (Hardware Cap)`
              : '8 GB (Hardware Cap)'}
          </span>
        </div>
      </div>
    </div>
  )
}
