# Autonomous PC Resource Management Agent

This project implements an intelligent multi-agent system that monitors system processes and automatically manages applications consuming excessive CPU or memory resources.

Built with the [SPADE](https://spade-mas.readthedocs.io/) multi-agent framework, [psutil](https://psutil.readthedocs.io/) for system monitoring, and [plyer](https://plyer.readthedocs.io/) for desktop notifications.

## Features

- Continuous periodic monitoring of all system processes
- Time-based decision making with process history tracking
- Automatic termination of processes with sustained high resource usage
- Multi-agent architecture with XMPP message passing
- Windows desktop toast notifications for critical events
- Color-coded console logging and persistent file logging
- Configurable thresholds, intervals, and critical process whitelist

## Project Structure

```
pc_resource_agent/
├── src/
│   ├── agents/
│   │   ├── monitor_agent.py   # Resource monitoring agent
│   │   └── alert_agent.py     # Desktop notification agent
│   └── core/
│       ├── monitor.py         # psutil process enumeration & termination
│       ├── history.py         # Per-process time-series tracking
│       ├── config.py          # Thresholds, intervals, whitelist
│       └── logger.py          # Dual-output color-coded logging
├── demo/
│   ├── stress_cpu.py          # CPU stress test for demos
│   └── stress_memory.py       # Memory stress test for demos
├── main.py                    # Entry point
├── requirements.txt
├── .env                       # XMPP credentials (not committed)
└── README.md
```

## Installation

1. Install Python 3.9 or higher
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your XMPP credentials:

```env
JID=your_monitor_agent@xmpp.jp
PASSWORD=your_password
ALERT_JID=your_alert_agent@xmpp.jp
ALERT_PASSWORD=your_alert_password
```

## Running the Agent

```bash
python main.py
```

The agent will begin monitoring system processes every few seconds.

## Logs

All system events and agent actions are recorded in `agent.log`.

## Stopping the Agent

Press `CTRL+C` in the terminal.
