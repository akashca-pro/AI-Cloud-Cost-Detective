"""In-memory WebSocket fan-out for live analysis progress (WP6)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

ProgressPayload = dict[str, Any]


class ProgressReporter:
    """Emit progress events to all WebSocket clients subscribed to an analysis_id."""

    def __init__(self, hub: ProgressHub, analysis_id: str) -> None:
        self._hub = hub
        self.analysis_id = analysis_id

    async def emit(
        self,
        step: str,
        message: str,
        *,
        status: str = "in_progress",
    ) -> None:
        await self._hub.broadcast(
            self.analysis_id,
            {
                "analysis_id": self.analysis_id,
                "step": step,
                "status": status,
                "message": message,
            },
        )


class ProgressHub:
    """Tracks WebSocket connections keyed by analysis_id."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, analysis_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(analysis_id, set()).add(websocket)
        logger.debug("WebSocket connected for analysis %s", analysis_id)

    async def disconnect(self, analysis_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            peers = self._connections.get(analysis_id)
            if not peers:
                return
            peers.discard(websocket)
            if not peers:
                self._connections.pop(analysis_id, None)
        logger.debug("WebSocket disconnected for analysis %s", analysis_id)

    async def broadcast(self, analysis_id: str, payload: ProgressPayload) -> None:
        async with self._lock:
            sockets = list(self._connections.get(analysis_id, set()))

        if not sockets:
            return

        dead: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)

        if dead:
            async with self._lock:
                peers = self._connections.get(analysis_id)
                if peers:
                    for websocket in dead:
                        peers.discard(websocket)
                    if not peers:
                        self._connections.pop(analysis_id, None)

    async def listen(self, analysis_id: str, websocket: WebSocket) -> None:
        """Keep the socket open until the client disconnects."""
        await self.connect(analysis_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await self.disconnect(analysis_id, websocket)


progress_hub = ProgressHub()
