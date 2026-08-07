import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Cpu, HardDrive, Zap, Shield, RefreshCw } from 'lucide-react'

export function HardwareMonitor() {
  const [vramUsage, setVramUsage] = useState(8.2) // MB
  const [tokensPerSec, setTokensPerSec] = useState(48.5)
  const [latency, setLatency] = useState(118)

  // Simulate dynamic low-amplitude hardware telemetry jitter
  useEffect(() => {
    const interval = setInterval(() => {
      setVramUsage((prev) => parseFloat((8.2 + (Math.random() * 0.4 - 0.2)).toFixed(1)))
      setTokensPerSec((prev) => parseFloat((48.5 + (Math.random() * 2.0 - 1.0)).toFixed(1)))
      setLatency((prev) => Math.floor(118 + (Math.random() * 8 - 4)))
    }, 2500)
    return () => clearInterval(interval)
  }, [])

  // Sample SVG Sparkline coordinates for smooth path
  const svgPathData = "M 0 60 Q 40 20, 80 55 T 160 30 T 240 65 T 320 40 T 400 50 L 400 100 L 0 100 Z"
  const svgLinePath = "M 0 60 Q 40 20, 80 55 T 160 30 T 240 65 T 320 40 T 400 50"

  return (
    <div className="hardware-monitor-card" id="hardware">
      <div className="monitor-header">
        <div className="monitor-title-group">
          <Cpu size={20} style={{ color: 'var(--accent-primary)' }} />
          <span>Hardware & VRAM Telemetry Monitor</span>
        </div>
        <span className="badge-vram-limit">MAX 8.0 GB VRAM</span>
      </div>

      <div className="hardware-metrics-grid">
        <div className="metric-tile">
          <span className="metric-tile-label">VRAM Allocated</span>
          <span className="metric-tile-value blue">{vramUsage} MB</span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Actor Model</span>
          <span className="metric-tile-value emerald">Llama-3.1 8B</span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Critic Model</span>
          <span className="metric-tile-value cyan">DeepSeek Coder</span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-label">Local Throughput</span>
          <span className="metric-tile-value amber">{tokensPerSec} tok/s</span>
        </div>
      </div>

      {/* SVG Animated Telemetry Sparkline */}
      <div className="chart-container-box">
        <div className="chart-meta-row">
          <span>Real-time Latency Waveform (~{latency}ms)</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--status-emerald)' }}>● Live Sampling</span>
        </div>

        <div className="svg-chart-wrapper">
          <svg viewBox="0 0 400 100" preserveAspectRatio="none">
            {/* Background solid Area overlay */}
            <path d={svgPathData} fill="#16203D" opacity="0.4" />
            {/* Animated Solid Line */}
            <motion.path
              d={svgLinePath}
              fill="none"
              stroke="#4F7CFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />
          </svg>
        </div>
      </div>

      {/* VRAM Progress Track */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <span>VRAM Footprint</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>0.1% Utilized</span>
        </div>
        <div className="vram-bar-track" style={{ height: '8px' }}>
          <div className="vram-bar-fill" style={{ width: '0.1%' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>0 GB</span>
          <span>4 GB</span>
          <span>8 GB (Hardware Cap)</span>
        </div>
      </div>
    </div>
  )
}
