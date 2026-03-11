# agent.py

import asyncio
import os

import dotenv
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

import config
import logger
import monitor
from history import ProcessHistory

dotenv.load_dotenv()
process_history = ProcessHistory()


class MonitorBehaviour(PeriodicBehaviour):
    async def run(self):

        logger.log_event("Scanning system processes...")

        processes = monitor.get_processes()

        for process in processes:
            pid = process["pid"]
            name = process["name"]
            cpu = process["cpu"]
            memory = process["memory"]

            # Skip critical processes
            if name in config.CRITICAL_PROCESSES:
                continue

            # Record this reading for history tracking
            process_history.record(pid, cpu, memory)

            # ---- DECISION LOGIC ----

            terminated = False

            if cpu > config.CPU_CRITICAL_THRESHOLD:
                duration = process_history.get_violation_duration(
                    pid, "cpu", config.CPU_CRITICAL_THRESHOLD
                )

                if process_history.is_sustained_cpu(pid):
                    logger.log_critical(
                        f"CRITICAL: {name} (PID {pid}) CPU at {cpu}% "
                        f"for {duration:.0f}s — terminating"
                    )
                    success = monitor.terminate_process(pid)

                    if success:
                        logger.log_event(f"Process {name} terminated.")
                        process_history.remove(pid)
                        terminated = True
                    else:
                        logger.log_warning(f"Failed to terminate {name}")
                else:
                    logger.log_warning(
                        f"{name} (PID {pid}) CPU at {cpu}% "
                        f"for {duration:.0f}s (threshold: {config.SUSTAINED_DURATION}s)"
                    )

            elif cpu > config.CPU_WARNING_THRESHOLD:
                logger.log_warning(f"WARNING: {name} CPU usage high ({cpu}%)")

            if not terminated and memory > config.MEMORY_CRITICAL_THRESHOLD:
                duration = process_history.get_violation_duration(
                    pid, "memory", config.MEMORY_CRITICAL_THRESHOLD
                )

                if process_history.is_sustained_memory(pid):
                    logger.log_critical(
                        f"CRITICAL MEMORY: {name} (PID {pid}) using {memory:.2f}% RAM "
                        f"for {duration:.0f}s — terminating"
                    )
                    success = monitor.terminate_process(pid)

                    if success:
                        logger.log_event(
                            f"Process {name} terminated due to memory usage."
                        )
                        process_history.remove(pid)
                    else:
                        logger.log_warning(f"Failed to terminate {name}")
                else:
                    logger.log_warning(
                        f"{name} (PID {pid}) memory at {memory:.2f}% "
                        f"for {duration:.0f}s (threshold: {config.SUSTAINED_DURATION}s)"
                    )


class ResourceManagementAgent(Agent):
    async def setup(self):

        logger.log_event("Resource Management Agent started.")

        monitor_behaviour = MonitorBehaviour(period=config.MONITOR_INTERVAL)

        self.add_behaviour(monitor_behaviour)


async def main():
    JID = os.getenv("JID")
    PASSWORD = os.getenv("PASSWORD")

    agent = ResourceManagementAgent(JID, PASSWORD)  # type: ignore

    await agent.start()

    logger.log_event("Agent running. Press CTRL+C to stop.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.log_event("Shutting down agent...")
        await agent.stop()
        logger.log_event("Agent stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
