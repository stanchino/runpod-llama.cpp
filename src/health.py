
import os
import subprocess
import requests
import psutil
import time
from datetime import datetime
from threading import Thread

# Global server state (as defined in handler.py)
server_process = None
health_stats = {
    "requests_processed": 0,
    "errors": 0,
    "last_request": None,
    "start_time": time.time()
}
model_loaded = False

def get_gpu_memory_info():
    """Get GPU memory usage using nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            used, total = map(int, result.stdout.strip().split(','))
            return {
                "used_mb": used,
                "total_mb": total,
                "usage_percent": round(used/total*100, 2)
            }
    except Exception as e:
        print(f"GPU memory check failed: {e}")
    return None

def check_llama_server_health():
    """Check if llama.cpp server is responding"""
    try:
        port = os.getenv("LLAMA_PORT", 1234)
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_comprehensive_health_status():
    """Generate comprehensive health status report"""
    global health_stats, model_loaded
    
    # System memory information
    memory_info = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # GPU information
    gpu_memory = get_gpu_memory_info()
    
    # Server status
    server_healthy = check_llama_server_health()
    
    # Calculate uptime
    uptime_seconds = time.time() - health_stats["start_time"]
    
    health_report = {
        "status": "healthy" if server_healthy and model_loaded else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "server": {
            "llama_cpp_ready": server_healthy,
            "model_loaded": model_loaded,
            "pid": server_process.pid if server_process else None
        },
        "system": {
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_mb": round(memory_info.total / (1024*1024), 2),
                "used_mb": round(memory_info.used / (1024*1024), 2),
                "usage_percent": memory_info.percent
            }
        },
        "gpu": gpu_memory,
        "statistics": {
            "requests_processed": health_stats["requests_processed"],
            "errors": health_stats["errors"],
            "last_request": health_stats["last_request"],
            "success_rate": round(
                (health_stats["requests_processed"] /
                max(health_stats["requests_processed"] + health_stats["errors"], 1)) * 100, 2
            )
        }
    }
    
    return health_report

# This function is meant to be used as a health check endpoint
def health_check():
    return get_comprehensive_health_status()
