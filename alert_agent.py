from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from plyer import notification

import logger


class AlertBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=10)

        if msg is None:
            return

        level = msg.get_metadata("level") or "info"
        body = msg.body

        if level == "critical":
            logger.log_critical(f"[ALERT] {body}")
        elif level == "warning":
            logger.log_warning(f"[ALERT] {body}")
        else:
            logger.log_event(f"[ALERT] {body}")

        notification.notify(
            title=f"Resource Agent — {level.upper()}",
            message=body,
            app_name="PC Resource Agent",
            timeout=10,
        )  # type: ignore


class AlertAgent(Agent):
    async def setup(self):
        logger.log_event("Alert Agent started. Waiting for messages...")
        self.add_behaviour(AlertBehaviour())
