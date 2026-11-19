"""
Real-time Mentor Feed WebSocket Endpoint
========================================
Maintains WebSocket connections for authenticated mentors and broadcasts
real-time IORI risk alerts and intervention events.
Includes a Redis Pub/Sub subscriber listening on 'coglearn:iori_alerts'.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_current_user_ws
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class MentorConnectionManager:
    """
    Manages active WebSocket connections for mentors, allowing targeted
    real-time event streaming and Redis Pub/Sub message relay.
    """

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._redis_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def connect(self, mentor_id: str, websocket: WebSocket) -> None:
        """Accepts and registers a new WebSocket connection."""
        await websocket.accept()
        if mentor_id not in self.active_connections:
            self.active_connections[mentor_id] = []
        self.active_connections[mentor_id].append(websocket)
        logger.info("WebSocket connected for mentor %s. Total connections: %d", mentor_id, len(self.active_connections[mentor_id]))

        # Ensure background Redis pub/sub listener is running
        self.ensure_redis_subscriber()

    def disconnect(self, mentor_id: str, websocket: WebSocket) -> None:
        """Removes a closed WebSocket connection."""
        if mentor_id in self.active_connections:
            if websocket in self.active_connections[mentor_id]:
                self.active_connections[mentor_id].remove(websocket)
            if not self.active_connections[mentor_id]:
                del self.active_connections[mentor_id]
        logger.info("WebSocket disconnected for mentor %s.", mentor_id)

    async def send_to_mentor(self, mentor_id: str, data: dict) -> None:
        """Sends a JSON payload to all active sockets of a specific mentor."""
        if mentor_id not in self.active_connections:
            return

        payload_str = json.dumps(data)
        dead_sockets = []

        for ws in self.active_connections[mentor_id]:
            try:
                await ws.send_text(payload_str)
            except Exception as exc:
                logger.warning("Error transmitting message to mentor %s: %s", mentor_id, exc)
                dead_sockets.append(ws)

        for dead_ws in dead_sockets:
            self.disconnect(mentor_id, dead_ws)

    async def broadcast_iori_alert(
        self,
        mentor_id: str,
        student_id: str,
        iori: float,
        risk_zone: str,
        additional_info: Optional[dict] = None,
    ) -> None:
        """Dispatches an IORI threshold alert payload to a mentor's active feed."""
        data = {
            "event": "iori_alert",
            "student_id": str(student_id),
            "iori_value": float(iori),
            "risk_zone": risk_zone,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": additional_info or {},
        }
        await self.send_to_mentor(mentor_id, data)

    def ensure_redis_subscriber(self) -> None:
        """Starts the Redis subscriber coroutine if not already running."""
        if self._redis_task is None or self._redis_task.done():
            self._running = True
            loop = asyncio.get_event_loop()
            self._redis_task = loop.create_task(self._redis_subscriber_loop())

    async def _redis_subscriber_loop(self) -> None:
        """Background coroutine listening to Redis Pub/Sub for IORI risk alerts."""
        try:
            import redis.asyncio as aioredis
        except ImportError:
            logger.warning("redis.asyncio not available. Real-time Redis pubsub disabled.")
            return

        while self._running:
            client = None
            try:
                client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                pubsub = client.pubsub()
                await pubsub.subscribe("coglearn:iori_alerts")
                logger.info("Subscribed to Redis channel 'coglearn:iori_alerts'.")

                while self._running:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        try:
                            payload = json.loads(message["data"])
                            target_mentor_id = str(payload.get("mentor_id"))
                            student_id = str(payload.get("student_id"))
                            iori = float(payload.get("iori", 0.0))
                            risk_zone = str(payload.get("risk_zone", "yellow"))

                            await self.broadcast_iori_alert(
                                mentor_id=target_mentor_id,
                                student_id=student_id,
                                iori=iori,
                                risk_zone=risk_zone,
                                additional_info=payload.get("details"),
                            )
                        except Exception as parse_exc:
                            logger.error("Failed to parse Redis alert payload: %s", parse_exc)

                    await asyncio.sleep(0.05)

            except Exception as conn_exc:
                logger.debug("Redis subscriber reconnecting in 5s: %s", conn_exc)
                await asyncio.sleep(5)
            finally:
                if client is not None:
                    try:
                        await client.aclose()
                    except Exception:
                        pass


manager = MentorConnectionManager()


async def mentor_ws_endpoint(
    websocket: WebSocket,
    mentor_id: str,
):
    """
    WebSocket endpoint handling real-time push events for an authorized mentor.
    Expects mentor authentication either via query parameter 'token' or headers.
    """
    # Authenticate WebSocket connection
    try:
        user: User = await get_current_user_ws(websocket=websocket)
        # Ensure user matches mentor_id or has admin authorization
        if str(user.id) != mentor_id and user.role.value not in ("inst_admin", "platform_admin"):
            await websocket.close(code=1008)
            return
    except Exception as auth_err:
        logger.warning("WebSocket auth failed for mentor %s: %s", mentor_id, auth_err)
        return

    await manager.connect(mentor_id, websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                action = data.get("action")
                if action == "ping":
                    await websocket.send_text(json.dumps({"action": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(mentor_id, websocket)
    except Exception as exc:
        logger.warning("WebSocket exception for mentor %s: %s", mentor_id, exc)
        manager.disconnect(mentor_id, websocket)
