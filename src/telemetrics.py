from datetime import datetime

import psutil
import requests


def generate_bar(percent, size=20):
    filled = int(percent * size / 100)
    return f"[{'■' * filled}{'-' * (size - filled)}]"


def get_process_by_name(name="uvicorn"):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if name in proc.info['name'] or \
                    any(name in cmd for cmd in proc.info['cmdline'] if cmd):
                return psutil.Process(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def format_bytes(bytes):
    """Convert bytes to MB with 1 decimal place"""
    return f"{bytes / (1024 * 1024):.1f}"


def monitor_process():
    WEBHOOK_URL = "https://discord.com/api/webhooks/1342891815283593318/3bh1fn_AOhPFeC1O-tWE4-1scsWh1K7nMtM8QSRXqlpk-RLObsHfRSqTi-UawqIclm8O"

    # Find the uvicorn process
    process = get_process_by_name("uvicorn")
    if not process:
        print("Process not found")
        return

    # Get process metrics
    with process.oneshot():  # More efficient collection of metrics
        # Basic process info
        cpu_percent = process.cpu_percent()
        mem_info = process.memory_full_info()

        # Memory details (in MB)
        rss = format_bytes(mem_info.rss)  # Physical memory
        vms = format_bytes(mem_info.vms)  # Virtual memory
        uss = format_bytes(mem_info.uss)  # Unique set size

        # Thread information
        threads = process.num_threads()
        thread_details = process.threads()

        # File descriptors
        try:
            fds = process.num_fds()
        except AttributeError:  # Windows systems
            fds = "N/A"

        # Connections
        connections = len(process.connections())

        # System memory info
        sys_mem = psutil.virtual_memory()
        sys_cpu = psutil.cpu_percent()

    # Create message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"""**System & Process Status** | {timestamp}
```
System:
CPU  : [{sys_cpu}%] {generate_bar(sys_cpu)}
RAM  : [{sys_mem.percent}%] {generate_bar(sys_mem.percent)} ({sys_mem.used >> 20}/{sys_mem.total >> 20}MB)

Python Process (PID: {process.pid}):
CPU Usage : [{cpu_percent}%] {generate_bar(cpu_percent)}
Memory:
  - RSS    : {rss}MB (Physical memory)
  - USS    : {uss}MB (Unique memory)
  - VMS    : {vms}MB (Virtual memory)
Activity:
  - Threads: {threads}
  - File descriptors: {fds}
  - Network connections: {connections}
```"""

    # Send to Discord
    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Discord: {e}")


if __name__ == "__main__":
    monitor_process()
