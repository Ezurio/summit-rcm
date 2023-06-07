"""
Module to support BLE data relay via WebSockets
"""

import asyncio
from collections import deque
from syslog import syslog
from typing import Deque, Dict
from uuid import uuid4
import falcon.asgi
import falcon
from summit_rcm.bluetooth.bt_ble import ble_notification_objects

SLEEP_DELAY_S = 0.1


class BluetoothWebSocketResource:
    """Resource to handle BLE via WebSocket"""

    def __init__(self) -> None:
        ble_notification_objects.append(self)
        self.listeners: Dict[str, Deque[str]] = {}

    def __del__(self):
        if self in ble_notification_objects:
            ble_notification_objects.remove(self)

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """Handle GET request"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"SDCERR": 0, "InfoMsg": ""}

    async def on_websocket(
        self, _: falcon.asgi.Request, websocket: falcon.asgi.WebSocket
    ):
        """Handle an incoming websocket connection"""
        try:
            if websocket.unaccepted:
                await websocket.accept()
        except falcon.WebSocketDisconnected:
            return

        # Create a message listener and add it to the dictionary
        listener_id = uuid4()
        message_listener = deque()
        self.listeners[listener_id] = message_listener

        # Create and start the 'sink' task
        sink_task = falcon.create_task(self.websocket_sink(websocket))

        # Loop while checking if we have any new messages to send
        while not sink_task.done():
            if len(message_listener) == 0:
                await asyncio.sleep(SLEEP_DELAY_S)
                continue

            try:
                await websocket.send_text(message_listener.popleft())
            except falcon.WebSocketDisconnected:
                break

        # Clean up sink task
        sink_task.cancel()
        try:
            await sink_task
        except asyncio.CancelledError:
            pass

        # Clean up message listener
        del self.listeners[listener_id]

    async def websocket_sink(self, websocket: falcon.asgi.WebSocket):
        """Handle incoming websocket messages"""

        while True:
            await asyncio.sleep(SLEEP_DELAY_S)

            try:
                # Receive any messages and just throw them away for now
                _ = await websocket.receive_text()
            except falcon.WebSocketDisconnected:
                break

    async def ble_notify(self, message: str | bytes):
        """Queue a message to be sent via a websocket connection if one is established"""
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            for _, listener in self.listeners.items():
                listener.append(str(message))
        except Exception as exception:
            syslog(f"ble_notify() - Could not send notification - {str(exception)}")
