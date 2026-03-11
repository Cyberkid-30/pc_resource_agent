# agent.py

import asyncio
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

import monitor
import config
import logger


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

            # ---- DECISION LOGIC ----

            if cpu > config.CPU_CRITICAL_THRESHOLD:
                logger.log_critical(f"CRITICAL: {name} (PID {pid}) CPU usage {cpu}%")

                success = monitor.terminate_process(pid)

                if success:
                    logger.log_event(f"Process {name} terminated.")
                else:
                    logger.log_warning(f"Failed to terminate {name}")

            elif cpu > config.CPU_WARNING_THRESHOLD:
                logger.log_warning(f"WARNING: {name} CPU usage high ({cpu}%)")

            if memory > config.MEMORY_CRITICAL_THRESHOLD:
                logger.log_critical(f"CRITICAL MEMORY: {name} using {memory:.2f}% RAM")

                success = monitor.terminate_process(pid)

                if success:
                    logger.log_event(f"Process {name} terminated due to memory usage.")
                else:
                    logger.log_warning(f"Failed to terminate {name}")


class ResourceManagementAgent(Agent):
    async def setup(self):

        logger.log_event("Resource Management Agent started.")

        monitor_behaviour = MonitorBehaviour(period=config.MONITOR_INTERVAL)

        self.add_behaviour(monitor_behaviour)


async def main():

    agent = ResourceManagementAgent("rescue_02@xmpp.jp", "123456")

    await agent.start()

    print("Agent running. Press CTRL+C to stop.")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Agent stopped.")
