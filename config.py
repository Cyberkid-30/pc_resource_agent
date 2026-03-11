# config.py

# Monitoring interval (seconds)
MONITOR_INTERVAL = 5

# CPU thresholds
CPU_WARNING_THRESHOLD = 50
CPU_CRITICAL_THRESHOLD = 80

# Memory threshold (percentage)
MEMORY_CRITICAL_THRESHOLD = 80

# Critical system processes that should NOT be terminated
CRITICAL_PROCESSES = [
    "System Idle Process",
    "System",
    "Registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "explorer.exe",
]
