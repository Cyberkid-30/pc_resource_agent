## Autonomous PC Resource Management Agent — Project Description

### 1. Project Overview

The **Autonomous PC Resource Management Agent** is a multi-agent system built in Python that continuously monitors operating system processes and autonomously manages applications consuming excessive CPU or memory resources. It uses the **SPADE (Smart Python Agent Development Environment)** multi-agent framework for agent orchestration and inter-agent communication over the XMPP protocol, and the **psutil** library for real-time system introspection.

The system is designed to run on **Windows** as a foreground console application. It operates in a continuous loop, scanning all running processes at a configurable interval, tracking resource usage over time, and making time-based decisions about whether to warn or terminate offending processes. Critical system processes are protected by a configurable whitelist. When a termination occurs, a desktop toast notification is delivered to the user via a dedicated Alert Agent.

### 2. System Architecture

The system follows a **multi-agent architecture** with two cooperating SPADE agents communicating via XMPP message passing:

| Agent | Role | SPADE Behaviour Type |
|---|---|---|
| **ResourceManagementAgent** (Monitor Agent) | Periodically scans system processes, tracks history, applies decision logic, terminates offending processes, sends alerts | `PeriodicBehaviour` |
| **AlertAgent** | Listens for incoming XMPP messages from the Monitor Agent and delivers Windows desktop toast notifications | `CyclicBehaviour` |

A separate **entry point** (main.py) initializes both agents, manages their lifecycle, and handles graceful shutdown.

#### 2.1 Component Diagram

```
┌──────────────────────────────────────────────────────┐
│                      main.py                         │
│              (Entry Point / Orchestrator)             │
│  - Loads environment variables                       │
│  - Starts AlertAgent, then ResourceManagementAgent   │
│  - Handles graceful shutdown on CTRL+C               │
└────────┬──────────────────────────┬──────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────────┐  ┌──────────────────────┐
│ ResourceManagement  │  │     AlertAgent       │
│      Agent          │  │  (alert_agent.py)    │
│ (monitor_agent.py)  │  │                      │
│                     │  │  AlertBehaviour       │
│ MonitorBehaviour    │──┤  (CyclicBehaviour)   │
│ (PeriodicBehaviour) │  │  - Receives XMPP msgs│
│ - Scans processes   │  │  - Shows Windows     │
│ - Tracks history    │  │    toast notification │
│ - Applies thresholds│  │  - Logs alerts       │
│ - Sends XMPP alerts │  └──────────────────────┘
│ - Terminates procs  │
└────┬───────┬────────┘
     │       │
     ▼       ▼
┌─────────┐ ┌──────────────┐
│monitor  │ │   history    │
│  .py    │ │    .py       │
│         │ │              │
│psutil   │ │ProcessHistory│
│wrapper  │ │(time-series  │
└─────────┘ │ per-PID)     │
            └──────────────┘
```

### 3. Module Descriptions

#### 3.1 main.py — Application Entry Point
- Loads credentials from environment variables via `python-dotenv`
- Instantiates and starts the `AlertAgent` first (so it is ready to receive messages), then the `ResourceManagementAgent`
- Maintains an async event loop (`asyncio.run`)
- Catches `KeyboardInterrupt` (CTRL+C) and calls `agent.stop()` on both agents for graceful SPADE shutdown

#### 3.2 monitor_agent.py — Resource Management Agent
- Defines `ResourceManagementAgent`, a SPADE `Agent` that registers a single `MonitorBehaviour`
- **`MonitorBehaviour`** (PeriodicBehaviour, period configurable):
  - Calls `monitor.get_processes()` to retrieve all running process snapshots
  - Skips processes in the `CRITICAL_PROCESSES` whitelist
  - Records each process's CPU and memory readings in `ProcessHistory`
  - **Decision logic** (three tiers for CPU):
    - **CPU > critical threshold AND sustained** → log critical, send XMPP alert to AlertAgent, terminate process
    - **CPU > critical threshold but NOT yet sustained** → log warning with current violation duration
    - **CPU > warning threshold** → log warning only
  - **Memory decision logic** (independent of CPU, but avoids double-termination):
    - **Memory > critical threshold AND sustained** → log critical, send alert, terminate
    - **Memory > critical threshold but NOT yet sustained** → log warning with duration
  - Uses `send_alert()` to construct a SPADE `Message` with metadata `level` (critical/warning/info) and sends it to the AlertAgent's JID

#### 3.3 alert_agent.py — Alert Notification Agent
- Defines `AlertAgent`, a SPADE `Agent` with a single `AlertBehaviour`
- **`AlertBehaviour`** (CyclicBehaviour):
  - Waits for incoming XMPP messages with a 10-second timeout
  - Reads the `level` metadata and message body from received messages
  - Logs the alert through the logger at the appropriate severity level
  - Dispatches a **Windows toast notification** via `plyer.notification` with the alert title, body, and app name

#### 3.4 monitor.py — System Process Monitor
- Wraps `psutil` for process enumeration and termination
- **CPU priming**: At import time, iterates all processes once to prime `cpu_percent()`. This is necessary because `psutil.cpu_percent()` returns 0.0 on its first call — it requires a previous measurement to compute elapsed CPU delta
- **`get_processes()`**: Returns a list of dictionaries (`pid`, `name`, `cpu`, `memory`) for all accessible system processes. Handles `NoSuchProcess` and `AccessDenied` exceptions gracefully
- **`terminate_process(pid)`**: Sends a `SIGTERM` to the target process via `psutil.Process.terminate()`. Returns `True` on success, `False` if the process no longer exists or access is denied

#### 3.5 history.py — Process History Tracker
- **`ProcessHistory`** class: Maintains a time-series of resource readings per PID using a `defaultdict(list)`
- **`record(pid, cpu, memory)`**: Appends a timestamped reading and prunes entries older than `HISTORY_WINDOW` (default: 60 seconds)
- **`is_sustained_cpu(pid)` / `is_sustained_memory(pid)`**: Returns `True` only if ALL readings within the last `SUSTAINED_DURATION` seconds (default: 15s) exceed the respective critical threshold, AND the time span of available data covers at least 80% of the sustained duration window — preventing false positives from insufficient data
- **`get_violation_duration(pid, metric, threshold)`**: Walks backward through the time-series to determine how many continuous seconds a process has been above the given threshold. Used for informational logging
- **`remove(pid)`**: Clears history for a terminated process

#### 3.6 config.py — Configuration Constants
| Parameter | Value | Description |
|---|---|---|
| `MONITOR_INTERVAL` | 5s | How often the monitor scans all processes |
| `CPU_WARNING_THRESHOLD` | 50% | CPU usage level that triggers a warning log |
| `CPU_CRITICAL_THRESHOLD` | 80% | CPU usage level considered critical |
| `MEMORY_CRITICAL_THRESHOLD` | 80% | Memory usage percentage considered critical |
| `HISTORY_WINDOW` | 60s | How long per-process readings are retained |
| `SUSTAINED_DURATION` | 15s | How long a violation must persist before termination |
| `CRITICAL_PROCESSES` | list of 10 | Windows system processes exempt from termination (e.g., `csrss.exe`, `lsass.exe`, `svchost.exe`, `explorer.exe`) |

#### 3.7 logger.py — Logging Module
- Configures a named Python logger (`ResourceAgent`) with two handlers:
  - **FileHandler**: Writes to agent.log with a timestamped plain-text format
  - **StreamHandler**: Outputs to the console with **color-coded formatting** via `colorama`:
    - Green for INFO
    - Yellow for WARNING
    - Bright Red for CRITICAL
- Exposes three convenience functions: `log_event()`, `log_warning()`, `log_critical()`

### 4. Communication Protocol

The Monitor Agent and Alert Agent communicate via **XMPP message passing** through the SPADE framework:

1. Monitor Agent constructs a `spade.message.Message` with:
   - `to`: The AlertAgent's XMPP JID (from environment variable `ALERT_JID`)
   - `body`: Human-readable description of the event (e.g., `"chrome.exe (PID 1234) CPU at 95% for 20s — terminating"`)
   - `metadata["level"]`: Severity string — `"critical"`, `"warning"`, or `"info"`
2. AlertAgent's `CyclicBehaviour` receives the message via `self.receive(timeout=10)`
3. AlertAgent maps the `level` metadata to the appropriate log severity and toast notification title

### 5. Decision-Making Flow

```
Process scanned
     │
     ├── In CRITICAL_PROCESSES whitelist? → Skip
     │
     ├── Record reading in ProcessHistory
     │
     ├── CPU > 80% (critical)?
     │     ├── Sustained ≥ 15s? → LOG CRITICAL + ALERT + TERMINATE
     │     └── Not sustained   → LOG WARNING (with duration)
     │
     ├── CPU > 50% (warning)? → LOG WARNING
     │
     └── Memory > 80% (critical) AND not already terminated?
           ├── Sustained ≥ 15s? → LOG CRITICAL + ALERT + TERMINATE
           └── Not sustained   → LOG WARNING (with duration)
```

### 6. Technology Stack

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| Agent Framework | SPADE | 4.1.2 |
| Messaging Protocol | XMPP (via slixmpp) | — |
| System Monitoring | psutil | 7.2.2 |
| Desktop Notifications | plyer | — |
| Console Colors | colorama | 0.4.6 |
| Environment Config | python-dotenv | — |
| Async Runtime | asyncio + winloop | 0.1.8 |

### 7. Environment Configuration

The system requires four XMPP credentials via a .env file:

| Variable | Purpose |
|---|---|
| `JID` | XMPP JID for the Resource Management Agent |
| `PASSWORD` | XMPP password for the Resource Management Agent |
| `ALERT_JID` | XMPP JID for the Alert Agent |
| `ALERT_PASSWORD` | XMPP password for the Alert Agent |

### 8. File Structure

```
pc_resource_agent/
├── main.py              # Entry point — starts and stops all agents
├── monitor_agent.py     # ResourceManagementAgent + MonitorBehaviour
├── alert_agent.py       # AlertAgent + AlertBehaviour
├── monitor.py           # psutil wrapper (process enumeration + termination)
├── history.py           # ProcessHistory (time-series tracking per PID)
├── config.py            # Thresholds, intervals, and critical process list
├── logger.py            # Dual-output color-coded logging
├── requirements.txt     # Pinned Python dependencies
├── .env                 # XMPP credentials (not committed)
└── agent.log            # Runtime log output (generated)
```

### 9. Key Design Decisions

1. **Time-based termination over single-spike reaction**: Processes are only terminated after sustained threshold violations (default 15s), preventing false positives from momentary CPU/memory spikes
2. **Multi-agent architecture with XMPP messaging**: Separates monitoring concerns from notification delivery. The AlertAgent can be extended or replaced independently (e.g., email, Slack)
3. **CPU measurement priming**: A one-time `process_iter` call at import resolves `psutil`'s first-call-returns-zero behavior
4. **Critical process whitelist**: Essential Windows system processes are protected from termination by name
5. **Double-termination prevention**: Memory check is skipped if the same process was already terminated by the CPU check in the same scan cycle
6. **Graceful shutdown**: CTRL+C triggers `agent.stop()` on both SPADE agents, allowing clean XMPP disconnection
