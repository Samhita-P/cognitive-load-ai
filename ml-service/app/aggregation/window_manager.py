import time
from collections import deque
from typing import Dict
from app.schemas.telemetry import TelemetryBatch

# In-memory session store
# session_id -> deque of TelemetryBatch (maxlen=6 for a 30s window composed of 5s batches)
session_windows: Dict[str, deque] = {}

# session_id -> timestamp of last batch received
session_last_active: Dict[str, float] = {}

def add_batch_to_window(batch: TelemetryBatch):
    """
    Adds a new 5s batch to the sliding window for the session.
    Returns the updated rolling window.
    """
    session_id = batch.session_id
    if session_id not in session_windows:
        session_windows[session_id] = deque(maxlen=6)
    
    session_windows[session_id].append(batch)
    session_last_active[session_id] = time.time()
    
    return session_windows[session_id]

def get_window(session_id: str):
    return session_windows.get(session_id, [])

def cleanup_inactive_sessions(timeout_minutes: int = 30):
    """
    Removes sessions that haven't received telemetry in a while.
    Called periodically to prevent memory leaks.
    """
    current_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    sessions_to_delete = [
        sid for sid, last_active in session_last_active.items()
        if current_time - last_active > timeout_seconds
    ]
    
    for sid in sessions_to_delete:
        del session_windows[sid]
        del session_last_active[sid]
        
    return len(sessions_to_delete)
