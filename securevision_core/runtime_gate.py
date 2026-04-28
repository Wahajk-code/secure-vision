import threading


_runtime_active_event = threading.Event()
_active_dashboard_connections = 0
_gate_lock = threading.Lock()


def activate_runtime() -> None:
    global _active_dashboard_connections
    with _gate_lock:
        _active_dashboard_connections += 1
        _runtime_active_event.set()


def deactivate_runtime() -> None:
    global _active_dashboard_connections
    with _gate_lock:
        if _active_dashboard_connections > 0:
            _active_dashboard_connections -= 1
        if _active_dashboard_connections == 0:
            _runtime_active_event.clear()


def wait_for_runtime(timeout: float | None = None) -> bool:
    return _runtime_active_event.wait(timeout=timeout)


def runtime_is_active() -> bool:
    return _runtime_active_event.is_set()


def active_connection_count() -> int:
    with _gate_lock:
        return _active_dashboard_connections
