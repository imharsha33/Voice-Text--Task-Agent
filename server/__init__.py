"""Server package for REST and WebSocket communication."""

from server.app import (
    app,
    start_server_background,
    update_status,
    broadcast_log,
    set_command_processor,
    set_listener_instance,
)

__all__ = [
    "app",
    "start_server_background",
    "update_status",
    "broadcast_log",
    "set_command_processor",
    "set_listener_instance",
]
