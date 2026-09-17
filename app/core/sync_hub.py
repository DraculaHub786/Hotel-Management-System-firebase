import queue
import threading
import time
import json
import logging
from typing import Dict, Set, List, Any, Optional

logger = logging.getLogger(__name__)

class EventSubscriber:
    """Thread-safe event subscriber queue with max-depth and drop-oldest policy."""
    def __init__(self, channels: Set[str], max_depth: int = 50):
        self.channels = set(channels)
        self.queue: queue.Queue = queue.Queue(maxsize=max_depth)
        self.created_at = time.time()
        self.active = True

    def put_event(self, event: dict):
        if not self.active:
            return
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            # Drop oldest policy
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.queue.put_nowait(event)
            except queue.Full:
                pass

class SyncHub:
    """In-memory room/channel-scoped event bus for live cross-role synchronization."""
    def __init__(self):
        self._subscribers: List[EventSubscriber] = []
        self._lock = threading.Lock()
        self._event_counter = 0

    def subscribe(self, channels: List[str], max_depth: int = 50) -> EventSubscriber:
        clean_channels = {c.strip() for c in channels if c and c.strip()}
        sub = EventSubscriber(clean_channels, max_depth=max_depth)
        with self._lock:
            self._subscribers.append(sub)
        return sub

    def unsubscribe(self, sub: EventSubscriber):
        sub.active = False
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def publish(self, channel: str, event_type: str, data: Optional[dict] = None) -> int:
        with self._lock:
            self._event_counter += 1
            event_id = self._event_counter
            active_subs = list(self._subscribers)

        payload = {
            "id": event_id,
            "channel": channel,
            "event": event_type,
            "data": data or {},
            "timestamp": time.time()
        }

        notified = 0
        for sub in active_subs:
            if not sub.active:
                continue
            if channel in sub.channels or '*' in sub.channels:
                sub.put_event(payload)
                notified += 1
            elif channel.startswith('guest:') and 'guest:*' in sub.channels:
                sub.put_event(payload)
                notified += 1

        return notified

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

# Global singleton instance
sync_hub = SyncHub()
