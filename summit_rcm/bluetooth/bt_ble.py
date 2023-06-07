"""
BLE BT plugin module
"""

import json
import os
import socket
from syslog import syslog
import threading
from time import time
from typing import Optional, Tuple, List
from dbus_fast.aio.proxy_object import ProxyInterface
import falcon.asgi
from summit_rcm.bluetooth.bt_module import (
    bt_device_services,
    bt_start_discovery,
    bt_stop_discovery,
    bt_connect,
    bt_disconnect,
    bt_read_characteristic,
    bt_write_characteristic,
    bt_config_characteristic_notification,
)
from summit_rcm.bluetooth.bt_module_extended import bt_init_ex
from summit_rcm.bluetooth.bt_ble_logger import BleLogger
from summit_rcm.bluetooth.bt_plugin import BluetoothPlugin
from summit_rcm.tcp_connection import (
    TcpConnection,
    TCP_SOCKET_HOST,
    SOCK_TIMEOUT,
)
from summit_rcm.utils import variant_to_python

discovery_keys = {"Name", "Alias", "Address", "Class", "Icon", "RSSI", "UUIDs"}

DEVICE_IFACE = "org.bluez.Device1"

ble_notification_objects: list = []

try:
    from summit_rcm.bluetooth.bt_ble_websocket import BluetoothWebSocketResource

    syslog("bt_ble: Bluetooth BLE Websockets loaded")
except ImportError:
    BluetoothWebSocketResource = None
    syslog("bt_ble: Bluetooth BLE Websockets NOT loaded")

websockets_auth_by_header_token: bool = BluetoothWebSocketResource is not None


class BluetoothBlePlugin(BluetoothPlugin):
    def __init__(self):
        self._server: Optional[BluetoothTcpServer] = None
        self._websockets_enabled: bool = False
        self.bt = None
        self.ble_logger: Optional[BleLogger] = None
        self.app: falcon.asgi.App = None

    @property
    def device_commands(self) -> List[str]:
        return ["bleConnect", "bleDisconnect", "bleGatt"]

    @property
    def adapter_commands(self) -> List[str]:
        adapter_commands = [
            "bleStartServer",
            "bleStopServer",
            "bleServerStatus",
            "bleStartDiscovery",
            "bleStopDiscovery",
        ]
        if BluetoothWebSocketResource:
            adapter_commands += ["bleEnableWebsockets"]
        return adapter_commands

    async def initialize(self):
        # Initialize the bluetooth manager
        if not self.bt:
            self.ble_logger = BleLogger(__name__)
            self.bt = await bt_init_ex(
                self.discovery_callback,
                self.characteristic_property_change_callback,
                self.connection_callback,
                self.write_notification_callback,
                logger=self.ble_logger,
                daemon=True,
                throw_exceptions=True,
            )
        # Enable websocket endpoint
        if BluetoothWebSocketResource and not self._websockets_enabled and self.app:
            try:
                self.app.add_route(
                    "/bluetoothWebsocket/ws", BluetoothWebSocketResource()
                )
                self._websockets_enabled = True
            except Exception as exception:
                self._websockets_enabled = False
                raise exception

    async def broadcast_ble_notification(self, message):
        if self._server:
            self._server.tcp_connection_try_send(message)
        for o in ble_notification_objects.copy():
            await o.ble_notify(message)

    def set_app(self, app: falcon.asgi.App):
        self.app = app

    async def ProcessDeviceCommand(
        self,
        bus,
        command,
        device_uuid: str,
        device_interface: Optional[ProxyInterface],
        adapter_interface: Optional[ProxyInterface],
        post_data,
        remove_device_method=None,
    ):
        processed = False
        error_message = None
        if command in self.device_commands and not self.bt:
            await self.initialize()
        if self.ble_logger:
            self.ble_logger.error_occurred = False
        if command == "bleConnect":
            processed = True
            await bt_connect(self.bt, device_uuid)
        elif command == "bleDisconnect":
            processed = True
            purge = False
            if "purge" in post_data:
                purge = post_data["purge"]
            await bt_disconnect(self.bt, device_uuid, purge)
        elif command == "bleGatt":
            processed = True
            if "svcUuid" not in post_data:
                return True, "svcUuid param not specified"
            if "chrUuid" not in post_data:
                return True, "charUuid param not specified"
            if "operation" not in post_data:
                return True, "operation param not specified"
            service_uuid = post_data["svcUuid"]
            char_uuid = post_data["chrUuid"]
            operation = post_data["operation"]
            if operation == "read":
                await bt_read_characteristic(
                    self.bt, device_uuid, service_uuid, char_uuid
                )
            elif operation == "write":
                if "value" not in post_data:
                    return True, "value param not specified"
                value = post_data["value"]
                value_bytes = bytearray.fromhex(value)
                await bt_write_characteristic(
                    self.bt, device_uuid, service_uuid, char_uuid, value_bytes
                )
            elif operation == "notify":
                if "enable" not in post_data:
                    return True, "enable param not specified"
                enable = post_data["enable"]
                await bt_config_characteristic_notification(
                    self.bt, device_uuid, service_uuid, char_uuid, enable
                )
            else:
                return True, f"unknown GATT operation {operation} requested"

        if self.ble_logger and self.ble_logger.error_occurred:
            error_message = self.ble_logger.last_message

        return processed, error_message

    async def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_interface: Optional[ProxyInterface],
        post_data,
    ) -> Tuple[bool, str, dict]:
        processed = False
        error_message = ""
        result = {}
        if self.ble_logger:
            self.ble_logger.error_occurred = False
        if BluetoothWebSocketResource and command == "bleEnableWebsockets":
            processed = True
            if not self._websockets_enabled:
                await self.initialize()
        elif command == "bleStartServer":
            processed = True
            if self._server:
                error_message = "bleServer already started"
            else:
                try:
                    self._server = BluetoothTcpServer()
                    error_message = self._server.connect(post_data)
                    if error_message:
                        self._server = None
                    else:
                        await self.initialize()
                except Exception as exception:
                    self._server = None
                    raise exception
        elif command == "bleServerStatus":
            processed = True
            if not self._server:
                result["started"] = False
            else:
                result["started"] = True
                result["port"] = self._server.port
        else:
            if command in self.adapter_commands and not self.bt:
                await self.initialize()
            if command == "bleStopServer":
                processed = True
                if self._server:
                    self._server.disconnect(bus, post_data)
                    self._server = None
                else:
                    error_message = "ble server is not running"
            elif command == "bleStartDiscovery":
                processed = True
                await bt_start_discovery(self.bt)
            elif command == "bleStopDiscovery":
                processed = True
                await bt_stop_discovery(self.bt)

        if self.ble_logger and self.ble_logger.error_occurred:
            error_message = self.ble_logger.last_message

        return processed, error_message, result

    async def discovery_callback(self, path, interfaces):
        """
        A callback that receives data about peripherals discovered by the bluetooth manager

        The data on each device is packaged as JSON and published on the
        'discovery' topic
        """
        for interface in interfaces.keys():
            if interface == DEVICE_IFACE:
                data = {}
                properties = interfaces[interface]
                for key in properties.keys():
                    if key in discovery_keys:
                        data[key] = variant_to_python(properties[key])
                data["timestamp"] = int(time())
                data = {"discovery": data}
                data_json = (
                    json.dumps(data, separators=(",", ":"), sort_keys=True, indent=4)
                    + "\n"
                )
                await self.broadcast_ble_notification(data_json.encode())

    async def connection_callback(self, data):
        """
        A callback that receives data about the connection status of devices

        Publishes connection status, and if connected, the device's services and
        characteristics to the 'connect' topic
        """
        if data["connected"]:
            # Get the services and characteristics of the connected device
            device_services = await bt_device_services(self.bt, data["address"])
            if device_services:
                data["services"] = device_services["services"]

        data["timestamp"] = int(time())
        data = {"connect": data}
        data_json = (
            json.dumps(data, separators=(",", ":"), sort_keys=True, indent=4) + "\n"
        )
        await self.broadcast_ble_notification(data_json.encode())

    async def write_notification_callback(self, data):
        """
        A callback that receives notifications on write operations to device
        characteristics and publishes the notification data to the 'gatt' topic
        """
        data["timestamp"] = int(time())
        data = {"char": data}
        data_json = json.dumps(data, separators=(",", ":"), indent=4) + "\n"
        await self.broadcast_ble_notification(data_json.encode())

    async def characteristic_property_change_callback(self, data):
        """
        A callback that receives notifications on a change to a connected device's
        characteristic properties and publishes the notification data to the 'gatt'
        topic
        """
        # Convert the changed value to hex
        temp = data["value"]
        data["value"] = "".join("{:02x}".format(x) for x in temp)
        data["timestamp"] = int(time())
        data = {"char": data}
        data_json = json.dumps(data, separators=(",", ":"), indent=4) + "\n"
        await self.broadcast_ble_notification(data_json.encode())


class BluetoothTcpServer(TcpConnection):
    """Serve up generic BLE
    profile and an associated TCP socket connection.
    """

    def __init__(self):
        self.recent_error: Optional[str] = None
        self.device_uuid: str = ""
        self.active_device_node: str = ""
        self.sock: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self._terminate_read_thread = False
        self._stop_pipe_r, self._stop_pipe_w = os.pipe()
        super().__init__()

    def connect(self, params=None):
        if not params or "tcpPort" not in params:
            return "tcpPort param not specified"

        port = params["tcpPort"]
        if not self.validate_port(int(port)):
            return f"port {port} not valid"

        self.sock = self.tcp_server(TCP_SOCKET_HOST, params)
        if not self.sock:
            return f"tcp server for port {port} could not start"

        self.thread = threading.Thread(
            target=self.bluetooth_tcp_server_thread,
            name="bluetooth_tcp_server_thread",
            daemon=True,
            args=(self.sock,),
        )
        self.thread.start()

        return ""

    def disconnect(self, bus, params=None):
        self.stop_tcp_server(self.sock)
        if self.thread:
            self.thread.join()

    def stop_read_thread(self):
        os.write(self._stop_pipe_w, b"c")

    def bluetooth_tcp_server_thread(self, sock):
        try:
            sock.settimeout(SOCK_TIMEOUT)
            while True:
                try:
                    tcp_connection, client_address = sock.accept()
                    with self._tcp_lock:
                        self._tcp_connection = tcp_connection
                    syslog(
                        "bluetooth_tcp_server_thread: tcp client connected:"
                        + str(client_address)
                    )
                    try:
                        # Wait on socket, such that closure will force exception and
                        # take us back to accept.
                        while self._tcp_connection.recv(16):
                            pass

                    except OSError as error:
                        # If sock is closed, exit.
                        if error.errno == socket.EBADF:
                            break
                        syslog("bluetooth_tcp_server_thread:" + str(error))
                    except Exception as error:
                        syslog(
                            "bluetooth_tcp_server_thread: non-OSError Exception: "
                            + str(error)
                        )
                        self.tcp_connection_try_send(
                            f'{{"Error": "{str(error)}"}}\n'.encode()
                        )
                    finally:
                        syslog(
                            "bluetooth_tcp_server_thread: tcp client disconnected:"
                            + str(client_address)
                        )
                        with self._tcp_lock:
                            self.close_tcp_connection()
                            self._tcp_connection, client_address = None, None
                except socket.timeout:
                    continue
                except OSError as error:
                    # If the socket was closed by another thread, exit
                    if error.errno == socket.EBADF:
                        break
                    else:
                        raise
        finally:
            sock.close()
            self._tcp_connection, client_address = None, None
