from datetime import datetime

import psutil
import requests


def generate_bar(percent, size=20):
    filled = int(percent * size / 100)
    return f"[{'■' * filled}{'-' * (size - filled)}]"


def format_bytes(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"


def monitor_process():
    WEBHOOK_URL = "https://discord.com/api/webhooks/1342891815283593318/3bh1fn_AOhPFeC1O-tWE4-1scsWh1K7nMtM8QSRXqlpk-RLObsHfRSqTi-UawqIclm8O"

    # System stats
    sys_mem = psutil.virtual_memory()
    sys_cpu = psutil.cpu_percent()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Call the debug endpoint
        debug_response = requests.get('http://localhost:1602/debug/memory', timeout=30)
        debug_data = debug_response.json()

        # Format the message
        message = f"""**Memory Profile** | {timestamp}
```
System Resources:
CPU  : [{sys_cpu}%] {generate_bar(sys_cpu)}
RAM  : [{sys_mem.percent}%] {generate_bar(sys_mem.percent)} ({sys_mem.used >> 20}/{sys_mem.total >> 20}MB)

Top Memory Allocations:"""

        # Add top memory allocations
        for alloc in debug_data['top_memory_allocations']:
            size = format_bytes(alloc['size'])
            message += f"\n• {alloc['file']}:{alloc['line']} - {size} ({alloc['count']} objects)"

        message += "\n\nObject Counts:"
        # Add top 5 object counts
        sorted_objects = sorted(debug_data['object_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
        for obj_type, count in sorted_objects:
            message += f"\n• {obj_type}: {count:,}"

        # Add total tracked memory
        total_tracked = format_bytes(debug_data['total_tracked_memory'][0])
        peak_tracked = format_bytes(debug_data['total_tracked_memory'][1])
        message += f"\n\nTotal Tracked Memory: {total_tracked}"
        message += f"\nPeak Tracked Memory: {peak_tracked}```"

    except requests.exceptions.RequestException as e:
        message = f"""**System Status** | {timestamp}
```
ERROR: Could not connect to debug endpoint: {str(e)}

System Resources:
CPU  : [{sys_cpu}%] {generate_bar(sys_cpu)}
RAM  : [{sys_mem.percent}%] {generate_bar(sys_mem.percent)} ({sys_mem.used >> 20}/{sys_mem.total >> 20}MB)
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
