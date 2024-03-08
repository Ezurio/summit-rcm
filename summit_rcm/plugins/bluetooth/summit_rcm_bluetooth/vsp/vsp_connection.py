"""
Module to support a Virtual Serial Port (VSP) between Bluetooth GATT Rx/Tx characteristics and
a TCP socket connection.
"""

import asyncio
import logging
from syslog import LOG_WARNING, syslog, LOG_INFO, LOG_ERR
from typing import Optional, Tuple, List, Dict
import dbus_fast
from dbus_fast.aio.proxy_object import ProxyInterface, ProxyObject
from summit_rcm_bluetooth.services.ble import (
    BLUEZ_SERVICE_NAME,
    GATT_CHRC_IFACE,
    DBUS_PROP_IFACE,
    GATT_SERVICE_IFACE,
    DBUS_OM_IFACE,
    DEVICE_IFACE,
    find_device,
    BLEWriteCharacteristicType,
    VSPSocketRxTypeEnum,
)
from summit_rcm_bluetooth.services.bt_plugin import BluetoothPlugin
from summit_rcm.tcp_connection import (
    TcpConnection,
    TCP_SOCKET_HOST,
)
from summit_rcm.dbus_manager import DBusManager
from summit_rcm.utils import variant_to_python

MAX_RECV_LEN = 512
""" Maximum bytes to read over TCP"""
DEFAULT_WRITE_SIZE = 1
""" Default GATT write size """


class VspConnection:
    """
    Represent a VSP connection with GATT read and write characteristics to a device, and an
    associated TCP socket connection.
    """

    def __init__(self, device_uuid: str, on_connection_closed=None):
        self.device_interface: Optional[ProxyInterface] = None
        self.adapter_interface: Optional[ProxyInterface] = None
        self.remove_device_method = None
        self._waiting_for_services_resolved: bool = False
        self.vsp_svc_uuid = None
        self.vsp_read_chrc: Optional[Tuple[ProxyObject, ProxyInterface]] = None
        self.vsp_read_chr_uuid = None
        self.vsp_write_chrc: Optional[Tuple[ProxyObject, ProxyInterface]] = None
        self.dev_props_iface: Optional[ProxyInterface] = None
        self.vsp_write_chr_uuid = None
        self.vsp_write_chr_type: str = ""
        self.socket_rx_type: VSPSocketRxTypeEnum = (
            VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON
        )
        self._logger = logging.getLogger(__name__)
        self.auth_failure_unpair = False
        self.write_size: int = DEFAULT_WRITE_SIZE
        self.device_uuid = device_uuid
        self.on_connection_closed = on_connection_closed
        self.rx_buffer: list = []
        self.server: Optional[asyncio.Server] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected: bool = False
        self.port: int = 0

    def log_exception(self, exception, message: str = ""):
        self._logger.exception(exception)
        syslog(LOG_ERR, message + str(exception))

    async def process_chrc(self, chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid):
        try:
            bus = await DBusManager().get_bus()
            chrc = bus.get_proxy_object(
                BLUEZ_SERVICE_NAME,
                chrc_path,
                await bus.introspect(BLUEZ_SERVICE_NAME, chrc_path),
            )
            chrc_iface = chrc.get_interface(GATT_CHRC_IFACE)

            uuid = variant_to_python(await chrc_iface.get_uuid())

            if uuid == vsp_read_chr_uuid:
                self.vsp_read_chrc = (chrc, chrc_iface)
            elif uuid == vsp_write_chr_uuid:
                self.vsp_write_chrc = (chrc, chrc_iface)

            return True
        except Exception:
            return False

    async def device_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if "Connected" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"VSP device_prop_changed_cb: Connected: "
                    f"{variant_to_python(changed_props['Connected'])}",
                )
                if (
                    self.writer
                    and self.socket_rx_type
                    == VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON
                ):
                    self.writer.write(
                        '{"Connected": '
                        f"{variant_to_python(changed_props['Connected'])}}}\n".encode()
                    )
            except Exception as exception:
                self.log_exception(exception)
        if (
            self.auth_failure_unpair
            and "DisconnectReason" in changed_props
            and changed_props["DisconnectReason"] == "auth failure"
        ):
            try:
                syslog(
                    LOG_INFO,
                    "VSP device_prop_changed_cb: disconnect auth failure, auto-unpairing",
                )
                if self.remove_device_method:
                    await self.remove_device_method(
                        self.adapter_interface, self.device_interface
                    )
            except Exception as exception:
                self.log_exception(exception)
        if "ServicesResolved" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"VSP device_prop_changed_cb: ServicesResolved: "
                    f"{variant_to_python(changed_props['ServicesResolved'])}",
                )
                if variant_to_python(changed_props["ServicesResolved"]):
                    if self._waiting_for_services_resolved:
                        self._waiting_for_services_resolved = False
                        await self.gatt_only_connected()
            except Exception as exception:
                self.log_exception(exception)

    def vsp_read_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if iface != GATT_CHRC_IFACE:
            syslog("vsp_read_prop_changed_cb: iface != GATT_CHRC_IFACE")

        if len(changed_props) == 0:
            return

        value = changed_props.get("Value", None)

        if value:
            self.gatt_vsp_read_val_cb(
                value.value if isinstance(value, dbus_fast.Variant) else value
            )

    def gatt_vsp_read_val_cb(self, value):
        try:
            if self.connected and self.writer:
                self.writer.write(
                    f'{{"Received": "0x{value.hex()}"}}\n'.encode()
                    if self.socket_rx_type
                    == VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON
                    else value
                )
        except OSError as error:
            syslog("gatt_vsp_read_val_cb:" + str(error))

    def generic_val_error_cb(self, error):
        syslog("generic_val_error_cb: D-Bus call failed: " + str(error))
        if "Not connected" in error.args:
            if (
                self.connected
                and self.writer
                and self.socket_rx_type
                == VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON
            ):
                self.writer.write('{"Connected": 0}\n'.encode())

    def gatt_vsp_write_val_error_cb(self, error):
        if (
            self.connected
            and self.socket_rx_type == VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON
            and self.writer
        ):
            self.writer.write('{"Error": "Transmit failed"}\n'.encode())
        self.generic_val_error_cb(error)

    async def start_client(self) -> bool:
        syslog("VSP: start_client")
        if not self.vsp_read_chrc:
            return False

        # Subscribe to VSP read value notifications.
        try:
            await self.vsp_read_chrc[1].call_start_notify()
            syslog("VSP: subscribed for GATT notifications")
        except dbus_fast.DBusError as error:
            syslog("VSP: unable to subscribe for GATT notifications")
            self.generic_val_error_cb(error)
            return False

        # Listen to PropertiesChanged signals from the Read Value
        # Characteristic.
        try:
            vsp_read_prop_iface = self.vsp_read_chrc[0].get_interface(DBUS_PROP_IFACE)
            vsp_read_prop_iface.on_properties_changed(self.vsp_read_prop_changed_cb)
        except Exception as exception:
            syslog(
                f"VSP: start_client, could not subscribe to read prop changes: {str(exception)}"
            )

        return True

    async def stop_client(self):
        # Stop client suppresses all errors, because it can be invoked during a failed startup,
        # in which case we want to focus attention on the startup error, not errors in
        # subsequently attempting to tear down.
        syslog("VSP: stop_client")
        vsp_read_prop_iface = None
        if self.vsp_read_chrc and len(self.vsp_read_chrc):
            try:
                vsp_read_prop_iface = self.vsp_read_chrc[0].get_interface(
                    DBUS_PROP_IFACE
                )
                await self.vsp_read_chrc[1].call_stop_notify()
            except Exception as exception:
                syslog(LOG_ERR, "stop_client: " + str(exception))
            self.vsp_read_chrc = None
        if vsp_read_prop_iface:
            try:
                vsp_read_prop_iface.off_properties_changed(
                    self.vsp_read_prop_changed_cb
                )
            except Exception as exception:
                syslog(LOG_ERR, "stop_client: " + str(exception))

    async def gatt_send_data(self, data) -> bool:
        try:
            if self.vsp_write_chrc and len(self.vsp_write_chrc):
                try:
                    await self.vsp_write_chrc[1].call_write_value(
                        bytearray(data),
                        (
                            {"type": self.vsp_write_chr_type}
                            if self.vsp_write_chr_type
                            else {}
                        ),
                    )
                    return True
                except dbus_fast.DBusError as error:
                    self.gatt_vsp_write_val_error_cb(error)
            return False
        except Exception as exception:
            syslog(LOG_ERR, f"VSP: gatt_send_data error: {str(exception)}")
            return False

    async def process_vsp_service(
        self,
        service_path,
        chrc_paths,
        vsp_svc_uuid,
        vsp_read_chr_uuid,
        vsp_write_chr_uuid,
    ):
        try:
            bus = await DBusManager().get_bus()
            service = bus.get_proxy_object(
                BLUEZ_SERVICE_NAME,
                service_path,
                await bus.introspect(BLUEZ_SERVICE_NAME, service_path),
            )
            service_iface = service.get_interface(GATT_SERVICE_IFACE)

            uuid = variant_to_python(await service_iface.get_uuid())

            if uuid != vsp_svc_uuid:
                raise Exception("Invalid UUID")

            # Process the characteristics.
            for chrc_path in chrc_paths:
                await self.process_chrc(
                    chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid
                )

            if self.vsp_read_chrc and self.vsp_write_chrc:
                vsp_service = (service, service_iface, service_path)
                return vsp_service
        except Exception:
            pass
        return None

    async def gatt_connect(
        self,
        bus,
        adapter_interface: ProxyInterface,
        device_interface: ProxyInterface,
        params=None,
        remove_device_method=None,
    ):
        if not params:
            return "no params specified"
        self.device_interface = device_interface
        self.adapter_interface = adapter_interface
        self.remove_device_method = remove_device_method
        if "authFailureUnpair" in params:
            self.auth_failure_unpair = params["authFailureUnpair"]
        if "vspSvcUuid" not in params:
            return "vspSvcUuid param not specified"
        self.vsp_svc_uuid = params["vspSvcUuid"]
        if "vspReadChrUuid" not in params:
            return "vspReachChrUuid param not specified"
        self.vsp_read_chr_uuid = params["vspReadChrUuid"]
        if "vspWriteChrUuid" not in params:
            return "vspWriteChrUuid param not specified"
        self.vsp_write_chr_uuid = params["vspWriteChrUuid"]
        if "tcpPort" not in params:
            return "tcpPort param not specified"
        try:
            self.port = int(params["tcpPort"])
            if not TcpConnection.validate_port(self.port):
                raise ValueError
        except ValueError:
            return "invalid value for tcpPort param"
        if "socketRxType" in params:
            try:
                self.socket_rx_type = VSPSocketRxTypeEnum(params["socketRxType"])
            except ValueError:
                return "invalid value for socketRxType param"
        if "vspWriteChrSize" in params:
            try:
                self.write_size = int(params["vspWriteChrSize"])
                if self.write_size < 1:
                    raise ValueError
            except ValueError:
                return "invalid value for vspWriteChrSize param"
        if "vspWriteChrType" in params:
            try:
                self.vsp_write_chr_type = BLEWriteCharacteristicType(
                    params["vspWriteChrType"]
                )
            except ValueError:
                return "invalid value for vspWriteChrType param"

        vsp_service = await self.create_vsp_service()
        if not vsp_service:
            return f"no VSP Service found for device {self.device_uuid}"

        if not await self.start_client():
            return "could not start GATT client"

        self.server = await asyncio.start_server(
            self.client_connected_callback,
            host=TCP_SOCKET_HOST,
            port=self.port,
            backlog=1,
        )

        self.dev_props_iface = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            self.device_interface.path,
            await bus.introspect(BLUEZ_SERVICE_NAME, self.device_interface.path),
        ).get_interface(DBUS_PROP_IFACE)
        self.dev_props_iface.on_properties_changed(self.device_prop_changed_cb)

        try:
            asyncio.create_task(self.server.serve_forever())
        except Exception as exception:
            syslog(
                f"VSP: gatt_connect() - error serving TCP connection - {str(exception)}"
            )

    async def gatt_only_disconnect(self):
        self.vsp_write_chrc: Optional[Tuple[ProxyObject, ProxyInterface]] = None
        try:
            self.dev_props_iface.off_properties_changed(self.device_prop_changed_cb)
            self.dev_props_iface = None
        except Exception as exception:
            syslog(LOG_ERR, "gatt_only_disconnect: " + str(exception))
        await self.stop_client()

    async def gatt_only_reconnect(self):
        """
        Reconnect VSP gatt connection, assuming it was prior connected and TCP server/
        websocket service is still running.
        Note: Services will NOT resolve if connect was not issued through LCM, as connect
        will not have been performed by controller_restore in that case.
        """
        bus = await DBusManager().get_bus()
        dev_obj_path, device_props = await find_device(bus, self.device_uuid)

        if not dev_obj_path:
            syslog(
                LOG_ERR,
                f"gatt_only_reconnect: device {self.device_uuid} not found on bus",
            )
            return
        self.device_interface = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            dev_obj_path,
            await bus.introspect(BLUEZ_SERVICE_NAME, dev_obj_path),
        ).get_interface(DEVICE_IFACE)

        self.dev_props_iface = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            dev_obj_path,
            await bus.introspect(BLUEZ_SERVICE_NAME, dev_obj_path),
        ).get_interface(DBUS_PROP_IFACE)
        self.dev_props_iface.on_properties_changed(self.device_prop_changed_cb)

        services_resolved = device_props.get("ServicesResolved")

        if services_resolved:
            await self.gatt_only_connected()
        else:
            syslog(
                LOG_INFO,
                f"services not resolved ({services_resolved}), schedule for "
                "later connection...",
            )
            self._waiting_for_services_resolved = True

    async def gatt_only_connected(self):
        syslog(LOG_INFO, f"gatt_only_connected {self.device_uuid}")
        vsp_service = await self.create_vsp_service()
        if not vsp_service:
            syslog(
                LOG_ERR,
                f"Failed to reconnect vsp_service for {self.device_uuid}",
            )
        if not await self.start_client():
            syslog(
                LOG_ERR,
                f"Failed to restart GATT client for {self.device_uuid}",
            )

    async def create_vsp_service(self):
        bus = await DBusManager().get_bus()
        om = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
        ).get_interface(DBUS_OM_IFACE)
        objects = await om.call_get_managed_objects()
        chrcs = []
        # List characteristics found
        for path, interfaces in objects.items():
            if GATT_CHRC_IFACE not in interfaces.keys():
                continue
            chrcs.append(path)
        # List sevices found
        vsp_service = None
        for path, interfaces in objects.items():
            if GATT_SERVICE_IFACE not in interfaces.keys():
                continue

            chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

            if not self.device_interface or path.startswith(self.device_interface.path):
                vsp_service = await self.process_vsp_service(
                    path,
                    chrc_paths,
                    self.vsp_svc_uuid,
                    self.vsp_read_chr_uuid,
                    self.vsp_write_chr_uuid,
                )
                if vsp_service:
                    break
        return vsp_service

    async def vsp_close(self):
        """
        Close the VSP connection down, including the REST host connection, and perform any necessary
        cleanup
        """
        # Signal to the VspConnectionPlugin that this VspConnection instance is closing
        if self.on_connection_closed:
            self.on_connection_closed(self)

        # Other cleanup
        self.connected = False
        await self.gatt_only_disconnect()
        self.server.close()
        syslog(LOG_INFO, f"VSP: closed for device {self.device_uuid}")

    async def client_connected_callback(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Callback fired when a client connects to the server socket.
        """

        # Log the connection
        addr = writer.get_extra_info("peername")
        syslog(f"VSP: TCP client connected: {addr!r}")

        # Expose the reader and writer to the rest of the class instance
        self.reader = reader
        self.writer = writer

        self.connected = True
        try:
            while self.connected:
                # Make sure the writer is in a good state
                await writer.drain()

                # Read some data
                data = await reader.read(self.write_size)
                if not data:
                    # When read() returns 0 bytes this indicates that the TCP client socket was
                    # closed
                    syslog(f"VSP: closing TCP client socket {addr!r}")
                    self.connected = False

                # Add the incoming data to the Rx buffer
                self.rx_buffer += data
                if len(self.rx_buffer) < self.write_size:
                    # Not enough data to transmit
                    continue

                # Send the data out via GATT
                success: bool = await self.gatt_send_data(
                    self.rx_buffer[: self.write_size]
                )

                # Update the Rx buffer to remove the now-sent chunk of data
                self.rx_buffer = self.rx_buffer[self.write_size :]

                # If the GATT Tx wasn't successful and the socket is configured for 'JSON', send a
                # notification to the TCP client.
                if not success and self.socket_rx_type == "JSON":
                    writer.write('{"Error": "Transmit failed"}\n'.encode())
        except Exception as exception:
            syslog(f"VSP: server_socket_event_handler error - {str(exception)}")

        # Perform any cleanup
        writer.close()
        await writer.wait_closed()
        await self.vsp_close()
        self.writer = None
        self.reader = None


class VspConnectionPlugin(BluetoothPlugin):
    def __init__(self):
        self.vsp_connections: Dict[str, VspConnection] = {}
        """Dictionary of devices by UUID and their associated VspConnection, if any"""

    @property
    def device_commands(self) -> List[str]:
        return ["gattConnect", "gattDisconnect"]

    @property
    def adapter_commands(self) -> List[str]:
        return ["gattList"]

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
        TIMEOUT_S: float = 5.0

        processed = False
        error_message = None
        if command == "gattConnect":
            processed = True
            if device_uuid in self.vsp_connections:
                error_message = (
                    f"device {device_uuid} already has vsp connection on port "
                    f"{self.vsp_connections[device_uuid].port}"
                )
            else:
                vsp_connection = VspConnection(device_uuid, self.on_connection_closed)
                try:
                    error_message = await asyncio.wait_for(
                        vsp_connection.gatt_connect(
                            bus,
                            adapter_interface,
                            device_interface,
                            post_data,
                            remove_device_method,
                        ),
                        timeout=TIMEOUT_S,
                    )
                except TimeoutError:
                    error_message = "command timed out"
                if not error_message:
                    self.vsp_connections[device_uuid] = vsp_connection
        elif command == "gattDisconnect":
            processed = True
            if device_uuid not in self.vsp_connections:
                error_message = f"device {device_uuid} has no vsp connection"
            else:
                syslog("Closing VSP due to gattDisconnect command")
                try:
                    await asyncio.wait_for(
                        self.vsp_connections[device_uuid].vsp_close(), timeout=TIMEOUT_S
                    )
                except TimeoutError:
                    syslog(LOG_WARNING, "VSP: close command timed out")
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
        if command == "gattList":
            processed = True
            result["GattConnections"] = [
                {"device": k, "port": self.vsp_connections[k].port}
                for k in self.vsp_connections.keys()
            ]
        return processed, error_message, result

    async def DeviceRemovedNotify(
        self, device_uuid: str, device_interface: ProxyInterface
    ):
        """Called when user has requested device be unpaired."""
        if device_uuid in self.vsp_connections:
            syslog("Closing VSP because the device was removed")
            await self.vsp_connections[device_uuid].vsp_close()

    async def ControllerRemovedNotify(
        self, controller_name: str, adapter_obj: ProxyObject
    ):
        for _, vsp_connection in self.vsp_connections.items():
            syslog("Controller removed, removing GATT change subscriptions")
            vsp_connection.gatt_only_disconnect()

    async def DeviceAddedNotify(
        self, device: str, device_uuid: str, device_obj: ProxyObject
    ):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            if vsp_uuid == device_uuid:
                syslog(f"Re-connecting GATT subscriptions for device {device_uuid}")
                await vsp_connection.gatt_only_reconnect()

    def on_connection_closed(self, connection: VspConnection) -> None:
        """
        Callback to be fired by the connection once it's closed
        """
        if connection.device_uuid in self.vsp_connections:
            self.vsp_connections.pop(connection.device_uuid)
