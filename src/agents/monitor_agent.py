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

        system_cpu = monitor.get_system_cpu()
        goal = config.SYSTEM_CPU_GOAL
        goal_met = system_cpu < goal

        if goal_met:
            logger.log_event(f"System CPU at {system_cpu}% — goal (<{goal}%) met.")
        else:
            logger.log_warning(
                f"System CPU at {system_cpu}% — EXCEEDS goal (<{goal}%). "
                "Scanning for offending processes..."
            )

        processes = monitor.get_processes()

        # Sort by CPU descending so we target the biggest offenders first
        processes.sort(key=lambda p: p["cpu"], reverse=True)

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

            # ---- GOAL-DRIVEN DECISION LOGIC ----

            terminated = False

            # When the system goal is NOT met, aggressively target
            # the highest CPU consumers with sustained usage
            if not goal_met and cpu > config.CPU_WARNING_THRESHOLD:
                duration = process_history.get_violation_duration(
                    pid, "cpu", config.CPU_WARNING_THRESHOLD
                )

                if process_history.is_sustained_cpu(pid):
                    alert_msg = (
                        f"GOAL VIOLATION: System CPU {system_cpu}% (goal <{goal}%). "
                        f"Terminating {name} (PID {pid}) at {cpu}% "
                        f"for {duration:.0f}s"
                    )
                    logger.log_critical(alert_msg)
                    await self.send_alert(alert_msg, level="critical")

                    success = monitor.terminate_process(pid)

                    if success:
                        logger.log_event(
                            f"Process {name} terminated to restore system goal."
                        )
                        process_history.remove(pid)
                        terminated = True
                    else:
                        logger.log_warning(f"Failed to terminate {name}")
                else:
                    logger.log_warning(
                        f"{name} (PID {pid}) CPU at {cpu}% "
                        f"for {duration:.0f}s — monitoring "
                        f"(system goal breached, threshold: {config.SUSTAINED_DURATION}s)"
                    )

            # Per-process critical threshold (applies even when goal IS met)
            elif cpu > config.CPU_CRITICAL_THRESHOLD:
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

            # Memory check (independent, avoids double-termination)
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

        logger.log_event(
            f"Resource Management Agent started. "
            f"Goal: maintain system CPU below {config.SYSTEM_CPU_GOAL}%."
        )

        monitor_behaviour = MonitorBehaviour(period=config.MONITOR_INTERVAL)

        self.add_behaviour(monitor_behaviour)
