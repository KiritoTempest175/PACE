import time
import typing

# Last recorded request performance metrics
_last_execution_telemetry: typing.Dict[str, typing.Any] = {
    "status": "idle",
    "latency_ms": None,
    "ttft_ms": None,
    "generation_time_s": None,
    "tokens_generated": None,
    "tokens_per_sec": None,
    "timestamp": None,
}


def update_last_execution_metrics(metrics: dict):
    global _last_execution_telemetry
    _last_execution_telemetry.update(metrics)


def get_system_telemetry() -> dict:
    vram_allocated_mb = None
    vram_total_mb = None
    vram_percent = None
    device_name = "CPU (Fallback)"
    gpu_utilization = None

    try:
        import torch

        if torch.cuda.is_available():
            vram_allocated_mb = float(torch.cuda.memory_allocated() / (1024**2))
            vram_total_mb = float(
                torch.cuda.get_device_properties(0).total_memory / (1024**2)
            )
            device_name = torch.cuda.get_device_name(0)
            if vram_total_mb > 0:
                vram_percent = round((vram_allocated_mb / vram_total_mb) * 100, 2)
            vram_allocated_mb = round(vram_allocated_mb, 1)
            vram_total_mb = round(vram_total_mb, 1)
    except Exception:
        pass

    cpu_utilization = None
    ram_usage_mb = None
    try:
        import psutil

        cpu_utilization = round(psutil.cpu_percent(interval=None), 1)
        ram_usage_mb = round(psutil.virtual_memory().used / (1024**2), 1)
    except Exception:
        pass

    actor_model = "PACE Actor 164M"
    critic_model = "Qwen 2.5-3B"

    return {
        "vram_allocated_mb": vram_allocated_mb,
        "vram_total_mb": vram_total_mb,
        "vram_percent": vram_percent,
        "gpu_utilization": gpu_utilization,
        "cpu_utilization": cpu_utilization,
        "ram_usage_mb": ram_usage_mb,
        "actor_model": actor_model,
        "critic_model": critic_model,
        "device": device_name,
        "status": _last_execution_telemetry.get("status", "idle"),
        "latency_ms": _last_execution_telemetry.get("latency_ms"),
        "ttft_ms": _last_execution_telemetry.get("ttft_ms"),
        "generation_time_s": _last_execution_telemetry.get("generation_time_s"),
        "tokens_generated": _last_execution_telemetry.get("tokens_generated"),
        "tokens_per_sec": _last_execution_telemetry.get("tokens_per_sec"),
        "timestamp": _last_execution_telemetry.get("timestamp"),
    }
