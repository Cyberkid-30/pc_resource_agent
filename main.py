import asyncio
import os

import dotenv

from src.core import logger
from src.agents.alert_agent import AlertAgent
from src.agents.monitor_agent import ResourceManagementAgent

dotenv.load_dotenv()


async def main():
    MONITOR_JID = os.getenv("MONITOR_JID")
    MONITOR_PASSWORD = os.getenv("MONITOR_PASSWORD")
    ALERT_JID = os.getenv("ALERT_JID")
    ALERT_PASSWORD = os.getenv("ALERT_PASSWORD")

    alert_agent = AlertAgent(ALERT_JID, ALERT_PASSWORD)  # type: ignore
    await alert_agent.start()

    monitor_agent = ResourceManagementAgent(MONITOR_JID, MONITOR_PASSWORD)  # type: ignore
    await monitor_agent.start()

    logger.log_event("Agents running. Press CTRL+C to stop.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.log_event("Shutting down agents...")
        await monitor_agent.stop()
        await alert_agent.stop()
        logger.log_event("Agents stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
