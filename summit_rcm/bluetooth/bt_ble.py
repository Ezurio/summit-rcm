import json
import os
import socket
import syslog
import threading
from time import time
from typing import Optional, Tuple, List

from .bt_module import (
    bt_device_services,
    bt_start_discovery,
    bt_stop_discovery,
    bt_connect,
    bt_disconnect,
    bt_read_characteristic,
    bt_write_characteristic,
    bt_config_characteristic_notification,
)
from .bt_module_extended import bt_init_ex
from .bt_ble_logger import BleLogger
from .bt_plugin import BluetoothPlugin
from ..tcp_connection import (
    TcpConnection,
    TCP_SOCKET_HOST,
    SOCK_TIMEOUT,
)

discovery_keys = {"Name", "Alias", "Address", "Class", "Icon", "RSSI", "UUIDs"}

DEVICE_IFACE = "org.bluez.Device1"

ble_notification_objects: list = []

try:
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from ws4py.websocket import WebSocket
    from .bt_ble_websocket import BluetoothWebsocket, BluetoothWebSocketHandler

    # cherrypy.log("bt_ble: Bluetooth BLE Websockets loaded")
    syslog("bt_ble: Bluetooth BLE Websockets loaded")
except ImportError:
    WebSocketPlugin = None
    # cherrypy.log("bt_ble: Bluetooth BLE Websockets NOT loaded")
    syslog("bt_ble: Bluetooth BLE Websockets NOT loaded")

websockets_auth_by_header_token: bool = WebSocketPlugin is not None


class BluetoothBlePlugin(BluetoothPlugin):
    def __init__(self):
        self._server: Optional[BluetoothTcpServer] = None
        self._websockets_enabled: bool = False
        self.bt = None
        self.ble_logger: Optional[BleLogger] = None

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
        if WebSocketPlugin:
            adapter_commands += ["bleEnableWebsockets"]
        return adapter_commands

    def initialize(self):
        # Initialize the bluetooth manager
        if not self.bt:
            self.ble_logger = BleLogger(__name__)
            self.bt = bt_init_ex(
                self.discovery_callback,
                self.characteristic_property_change_callback,
                self.connection_callback,
                self.write_notification_callback,
                logger=self.ble_logger,
                daemon=True,
                throw_exceptions=True,
            )
        # Enable websocket endpoint
        if WebSocketPlugin and not self._websockets_enabled:
            try:
                WebSocketPlugin(cherrypy.engine).subscribe()
                cherrypy.tools.websocket = WebSocketTool()
                cherrypy.tree.mount(
                    BluetoothWebsocket(),
                    "/bluetoothWebsocket",
                    config={
                        "/": {"tools.sessions.on": websockets_auth_by_header_token},
                        "/ws": {
                            "tools.sessions.on": websockets_auth_by_header_token,
                            "tools.websocket.on": True,
                            "tools.websocket.handler_cls": BluetoothWebSocketHandler,
                        },
                    },
                )
                self._websockets_enabled = True
            except Exception as e:
                self._websockets_enabled = False
                raise e

    def broadcast_ble_notification(self, message):
        if self._server:
            self._server.tcp_connection_try_send(message)
        for o in ble_notification_objects.copy():
            o.ble_notify(message)

    def ProcessDeviceCommand(
        self, bus, command, device_uuid: str, device: str, post_data
    ):
        processed = False
        error_message = None
        if command in self.device_commands and not self.bt:
            self.initialize()
        if self.ble_logger:
            self.ble_logger.error_occurred = False
        if command == "bleConnect":
            processed = True
            bt_connect(self.bt, device_uuid)
        elif command == "bleDisconnect":
            processed = True
            purge = False
            if "purge" in post_data:
                purge = post_data["purge"]
            bt_disconnect(self.bt, device_uuid, purge)
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
                bt_read_characteristic(self.bt, device_uuid, service_uuid, char_uuid)
            elif operation == "write":
                if "value" not in post_data:
                    return True, "value param not specified"
                value = post_data["value"]
                value_bytes = bytearray.fromhex(value)
                bt_write_characteristic(
                    self.bt, device_uuid, service_uuid, char_uuid, value_bytes
                )
            elif operation == "notify":
                if "enable" not in post_data:
                    return True, "enable param not specified"
                enable = post_data["enable"]
                bt_config_characteristic_notification(
                    self.bt, device_uuid, service_uuid, char_uuid, enable
                )
            else:
                return True, f"unknown GATT operation {operation} requested"

        if self.ble_logger and self.ble_logger.error_occurred:
            error_message = self.ble_logger.last_message

        return processed, error_message

    def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_obj: str,
        post_data,
    ) -> Tuple[bool, str, dict]:
        processed = False
        error_message = ""
        result = {}
        if self.ble_logger:
            self.ble_logger.error_occurred = False
        if WebSocketPlugin and command == "bleEnableWebsockets":
            processed = True
            if not self._websockets_enabled:
                self.initialize()
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
                        self.initialize()
                except Exception as e:
                    self._server = None
                    raise e
        elif command == "bleServerStatus":
            processed = True
            if not self._server:
                result["started"] = False
            else:
                result["started"] = True
                result["port"] = self._server.port
        else:
            if command in self.adapter_commands and not self.bt:
                self.initialize()
            if command == "bleStopServer":
                processed = True
                if self._server:
                    self._server.disconnect(bus, post_data)
                    self._server = None
                else:
                    error_message = "ble server is not running"
            elif command == "bleStartDiscovery":
                processed = True
                bt_start_discovery(self.bt)
            elif command == "bleStopDiscovery":
                processed = True
                bt_stop_discovery(self.bt)

        if self.ble_logger and self.ble_logger.error_occurred:
            error_message = self.ble_logger.last_message

        return processed, error_message, result

    def discovery_callback(self, path, interfaces):
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
                        data[key] = properties[key]
                data["timestamp"] = int(time())
                data = {"discovery": data}
                data_json = (
                    json.dumps(data, separators=(",", ":"), sort_keys=True, indent=4)
                    + "\n"
                )
                self.broadcast_ble_notification(data_json.encode())

    def connection_callback(self, data):
        """
        A callback that receives data about the connection status of devices

        Publishes connection status, and if connected, the device's services and
        characteristics to the 'connect' topic
        """
        if data["connected"]:
            # Get the services and characteristics of the connected device
            device_services = bt_device_services(self.bt, data["address"])
            if device_services:
                data["services"] = device_services["services"]

        data["timestamp"] = int(time())
        data = {"connect": data}
        data_json = (
            json.dumps(data, separators=(",", ":"), sort_keys=True, indent=4) + "\n"
        )
        self.broadcast_ble_notification(data_json.encode())

    def write_notification_callback(self, data):
        """
        A callback that receives notifications on write operations to device
        characteristics and publishes the notification data to the 'gatt' topic
        """
        data["timestamp"] = int(time())
        data = {"char": data}
        data_json = json.dumps(data, separators=(",", ":"), indent=4) + "\n"
        self.broadcast_ble_notification(data_json.encode())

    def characteristic_property_change_callback(self, data):
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
        self.broadcast_ble_notification(data_json.encode())


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

                    except OSError as e:
                        # If sock is closed, exit.
                        if e.errno == socket.EBADF:
                            break
                        syslog("bluetooth_tcp_server_thread:" + str(e))
                    except Exception as e:
                        syslog(
                            "bluetooth_tcp_server_thread: non-OSError Exception: "
                            + str(e)
                        )
                        self.tcp_connection_try_send(
                            f'{{"Error": "{str(e)}"}}\n'.encode()
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
                except OSError as e:
                    # If the socket was closed by another thread, exit
                    if e.errno == socket.EBADF:
                        break
                    else:
                        raise
        finally:
            sock.close()
            self._tcp_connection, client_address = None, None
