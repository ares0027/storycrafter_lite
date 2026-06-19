import psutil
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False

from models import PerformanceStats

def get_system_stats() -> dict:
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    ram = vm.used / (1024 * 1024) # MB
    ram_total = vm.total / (1024 * 1024)
    
    gpu = None
    vram = None
    vram_total = None
    
    if NVML_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu = float(util.gpu)
            vram = meminfo.used / (1024 * 1024)
            vram_total = meminfo.total / (1024 * 1024)
        except Exception:
            pass
            
    return {
        "cpu_usage_percent": cpu,
        "ram_usage_mb": ram,
        "ram_total_mb": ram_total,
        "gpu_usage_percent": gpu,
        "vram_usage_mb": vram,
        "vram_total_mb": vram_total
    }

def calculate_performance(start_time: float, end_time: float, tokens_sent: int, tokens_received: int) -> PerformanceStats:
    total_time = end_time - start_time
    tps = tokens_received / total_time if total_time > 0 else 0.0
    
    sys_stats = get_system_stats()
    
    return PerformanceStats(
        cpu_usage_percent=sys_stats["cpu_usage_percent"],
        ram_usage_mb=sys_stats["ram_usage_mb"],
        gpu_usage_percent=sys_stats["gpu_usage_percent"],
        vram_usage_mb=sys_stats["vram_usage_mb"],
        tokens_sent=tokens_sent,
        tokens_received=tokens_received,
        total_time_seconds=total_time,
        tokens_per_second=tps
    )
