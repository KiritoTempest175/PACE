// Global event bus for real-time AI hardware telemetry
class TelemetryStore {
  constructor() {
    this.listeners = new Set()
    this.latestTelemetry = null
  }

  subscribe(listener) {
    this.listeners.add(listener)
    if (this.latestTelemetry) {
      listener(this.latestTelemetry)
    }
    return () => {
      this.listeners.delete(listener)
    }
  }

  emit(telemetryData) {
    this.latestTelemetry = telemetryData
    for (const listener of this.listeners) {
      try {
        listener(telemetryData)
      } catch (err) {
        console.error("Telemetry listener error:", err)
      }
    }
  }
}

export const telemetryStore = new TelemetryStore()
