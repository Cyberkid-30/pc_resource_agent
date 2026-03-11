# ---- AGENT GOAL ----
# The agent's primary objective: keep overall system CPU below this target
SYSTEM_CPU_GOAL = 75  # percentage

# Monitoring interval (seconds)
MONITOR_INTERVAL = 5

# CPU thresholds (per-process)
CPU_WARNING_THRESHOLD = 50
CPU_CRITICAL_THRESHOLD = 80

# Memory threshold (percentage)
MEMORY_CRITICAL_THRESHOLD = 80

# History tracking
HISTORY_WINDOW = 60  # seconds of history to keep per process
SUSTAINED_DURATION = 15  # seconds a process must exceed threshold before termination

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
