"""Scan progress events — Redis pub/sub + in-memory queues for WebSocket clients."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from app.core.config import settings

_memory_queues: dict[int, list[asyncio.Queue]] = {}


def _redis_publish(scan_id: int, message: str) -> None:
    try:
        import redis

        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.publish(f"scan:{scan_id}", message)
        client.close()
    except Exception:
        pass


def publish_scan_event(scan_id: int, payload: Dict[str, Any]) -> None:
    message = json.dumps({"scan_id": scan_id, **payload})
    _redis_publish(scan_id, message)
    for queue in _memory_queues.get(scan_id, []):
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass


def register_listener(scan_id: int) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _memory_queues.setdefault(scan_id, []).append(queue)
    return queue


def unregister_listener(scan_id: int, queue: asyncio.Queue) -> None:
    queues = _memory_queues.get(scan_id, [])
    if queue in queues:
        queues.remove(queue)
    if not queues:
        _memory_queues.pop(scan_id, None)


async def forward_redis_to_queue(scan_id: int, queue: asyncio.Queue) -> None:
    """Subscribe to Redis and push messages into the local queue (for Celery workers)."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        pubsub = r.pubsub()
        await pubsub.subscribe(f"scan:{scan_id}")
        async for msg in pubsub.listen():
            if msg.get("type") == "message":
                await queue.put(msg["data"])
    except Exception:
        return
