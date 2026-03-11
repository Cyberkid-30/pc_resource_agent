import os

import dotenv
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from src.core import config, logger, monitor
from src.core.history import ProcessHistory

dotenv.load_dotenv()
process_history = ProcessHistory()


class MonitorBehaviour(PeriodicBehaviour):
    async def send_alert(self, body, level="info"):
        alert_jid = os.getenv("ALERT_JID")
        msg = Message(to=alert_jid)
        msg.body = body
        msg.set_metadata("level", level)
        await self.send(msg)

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
                    alert_msg = (
                        f"{name} (PID {pid}) CPU at {cpu}% "
                        f"for {duration:.0f}s — terminating"
                    )
                    logger.log_critical(f"CRITICAL: {alert_msg}")
                    await self.send_alert(alert_msg, level="critical")

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
                    alert_msg = (
                        f"{name} (PID {pid}) using {memory:.2f}% RAM "
                        f"for {duration:.0f}s — terminating"
                    )
                    logger.log_critical(f"CRITICAL MEMORY: {alert_msg}")
                    await self.send_alert(alert_msg, level="critical")

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
