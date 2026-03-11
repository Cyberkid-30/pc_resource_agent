# Autonomous PC Resource Management Agent

This project implements an intelligent agent that monitors system processes and automatically manages applications that consume excessive CPU or memory.

The system was developed using the [SPADE](https://spade-mas.readthedocs.io/) agent framework and the [psutil](https://psutil.readthedocs.io/) library for system monitoring.

## Features

- Continuous monitoring of system processes
- Detection of high CPU or memory usage
- Automatic termination of problematic processes
- Logging of agent actions and events

## Installation

1. Install Python 3.9 or higher
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Agent

Run the following command:

```bash
python agent.py
```

The agent will begin monitoring system processes every few seconds.

## Logs

All system events and agent actions are recorded in `agent.log`.

## Stopping the Agent

Press `CTRL+C` in the terminal.
