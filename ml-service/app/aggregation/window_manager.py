import time
import threading
from collections import deque, defaultdict
from typing import Dict
from app.schemas.telemetry import TelemetryBatch

# In-memory session store
session_windows: Dict[str, deque] = {}
session_last_active: Dict[str, float] = {}

import asyncio
import logging

logger = logging.getLogger(__name__)

# Per-session locks to avoid blocking concurrent inferences for different users
_session_locks: Dict[str, threading.Lock] = {}

# Global lock only used during dictionary structural changes (eviction)
_global_lock = threading.Lock()

def add_batch_to_window(batch: TelemetryBatch):
    """
    Adds a new 5s batch to the sliding window for the session.
    Returns the updated rolling window.
    """
    session_id = batch.session_id
    
    with _global_lock:
        if session_id not in _session_locks:
            _session_locks[session_id] = threading.Lock()
        lock = _session_locks[session_id]
        
    with lock:
        if session_id not in session_windows:
            session_windows[session_id] = deque(maxlen=6)
        
        session_windows[session_id].append(batch)
        session_last_active[session_id] = time.time()
        
        return list(session_windows[session_id])

def get_window(session_id: str):
    with _global_lock:
        if session_id not in _session_locks:
            return []
        lock = _session_locks[session_id]
    with lock:
        return list(session_windows.get(session_id, []))

def cleanup_inactive_sessions(timeout_minutes: int = 30):
    """
    Removes sessions that haven't received telemetry in a while.
    Called periodically to prevent memory leaks.
    """
    current_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    with _global_lock:
        sessions_to_delete = [
            sid for sid, last_active in session_last_active.items()
            if current_time - last_active > timeout_seconds
        ]
        
        for sid in sessions_to_delete:
            lock = _session_locks[sid]
            with lock:
                session_windows.pop(sid, None)
                session_last_active.pop(sid, None)
            _session_locks.pop(sid, None)
            
    return len(sessions_to_delete)

async def periodic_cleanup(timeout_minutes: int = 30, interval_seconds: int = 300):
    """
    Background task to periodically clean up inactive sessions.
    """
    logger.info(f"Started periodic session cleanup task (every {interval_seconds}s)")
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            cleaned = cleanup_inactive_sessions(timeout_minutes)
            if cleaned > 0:
                logger.info(f"Periodic cleanup evicted {cleaned} inactive sessions.")
    except asyncio.CancelledError:
        logger.info("Periodic session cleanup task cancelled.")
