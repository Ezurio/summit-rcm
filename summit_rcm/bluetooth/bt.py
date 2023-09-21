"""
Module for controlling/interface with Bluetooth devices
"""

import asyncio
import itertools
import logging
import re
from syslog import syslog, LOG_ERR, LOG_INFO
from typing import Any, Optional, List, Dict
from dbus_fast import Message, MessageType, Variant
from dbus_fast.aio.proxy_object import ProxyInterface
import falcon
from summit_rcm.dbus_manager import DBusManager
from summit_rcm.bluetooth import bt_plugin
from summit_rcm import definition
from summit_rcm.bluetooth.ble import (
    DBUS_PROP_IFACE,
    controller_pretty_name,
    find_device,
    DEVICE_IFACE,
    ADAPTER_IFACE,
    DBUS_OM_IFACE,
    AgentSingleton,
    BLUEZ_SERVICE_NAME,
    uri_to_uuid,
    GATT_MANAGER_IFACE,
    create_agent_singleton,
)
from summit_rcm.bluetooth.bt_controller_state import BluetoothControllerState
from summit_rcm.utils import Singleton, variant_to_python


PAIR_TIMEOUT_SECONDS = 60
CONNECT_TIMEOUT_SECONDS = 60

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [
    ("Trusted", bool, "b"),
    ("AutoConnect", bool, "b"),
    ("AutoConnectAutoDisable", bool, "b"),
]

CACHED_DEVICE_PROPS = ["connected", "autoConnect", "autoConnectAutoDisable"]

# These controller properties can be directly set, without requiring any special-case logic.
PASS_ADAPTER_PROPS = ["Discovering", "Powered", "Discoverable"]

# Additionally transportFilter is cached, but by special-case logic that confirms
# value is accepted.
CACHED_ADAPTER_PROPS = ["discovering", "powered", "discoverable"]

ADAPTER_PATH_PATTERN = re.compile("^/org/bluez/hci\\d+$")
DEVICE_PATH_PATTERN = re.compile("^/org/bluez/hci\\d+/dev_\\w+$")
DEVICE_ADAPTER_GROUP_PATTERN = re.compile("^(/org/bluez/hci\\d+)/dev_\\w+$")

bluetooth_plugins: List[bt_plugin.BluetoothPlugin] = []

try:
    from summit_rcm.hid.barcode_scanner import HidBarcodeScannerPlugin

    hid_barcode_scanner_plugin = HidBarcodeScannerPlugin()
    if hid_barcode_scanner_plugin not in bluetooth_plugins:
        bluetooth_plugins.append(hid_barcode_scanner_plugin)
    syslog("bluetooth: HidBarcodeScannerPlugin loaded")
except ImportError:
    syslog("bluetooth: HidBarcodeScannerPlugin NOT loaded")

try:
    from summit_rcm.vsp.vsp_connection import VspConnectionPlugin

    vsp_connection_plugin = VspConnectionPlugin()
    if vsp_connection_plugin not in bluetooth_plugins:
        bluetooth_plugins.append(vsp_connection_plugin)
    syslog("bluetooth: VspConnectionPlugin loaded")
except ImportError:
    syslog("bluetooth: VspConnectionPlugin NOT loaded")

try:
    bluetooth_ble_plugin = None
    from summit_rcm.bluetooth.bt_ble import BluetoothBlePlugin

    bluetooth_ble_plugin = BluetoothBlePlugin()
    if bluetooth_ble_plugin not in bluetooth_plugins:
        bluetooth_plugins.append(bluetooth_ble_plugin)
    syslog("bluetooth: BluetoothBlePlugin loaded")
except ImportError:
    syslog("bluetooth: BluetoothBlePlugin NOT loaded")


async def get_controller_obj(controller: str = ""):
    result = {}
    # get the system bus
    bus = await DBusManager().get_bus()
    # get the ble controller
    if not controller:
        result[
            "InfoMsg"
        ] = f"Controller {controller_pretty_name(controller)} not found."
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1)
        controller_obj = None
    else:
        controller_obj = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            controller,
            await bus.introspect(BLUEZ_SERVICE_NAME, controller),
        )

    return bus, controller_obj, result


def lower_camel_case(upper_camel_string: str):
    """Return supplied UpperCamelCase string in lowerCamelCase"""
    return upper_camel_string[:1].lower() + upper_camel_string[1:]


class Bluetooth(metaclass=Singleton):
    def __init__(self):
        self._controller_states: Dict[str, BluetoothControllerState] = {}
        """Controller state tracking - indexed by friendly (REST API) name"""
        self._controller_addresses: Dict[str, str] = {}
        """Controller addresses - indexed by friendly (REST API) name"""
        self._controller_callbacks_registered = False
        self._logger = logging.getLogger(__name__)
        self._devices_to_restore: Dict[str, type(None)] = {}
        """Map of device uuids to restore state due to associated controller reset"""
        self.setup_initiated: bool = False

    async def setup(self, app: falcon.asgi.App) -> None:
        """
        Run async logic required to setup Bluetooth intergration
        """
        if not self.setup_initiated:
            self.setup_initiated = True
            for plugin in bluetooth_plugins:
                if isinstance(plugin, BluetoothBlePlugin):
                    plugin.set_app(app)
                    break
            await self.discover_controllers()

    def add_ws_route(self, ws_route: str, is_legacy: bool = False):
        """Add a websocket route to the list of supported routes"""
        for plugin in bluetooth_plugins:
            if isinstance(plugin, BluetoothBlePlugin):
                plugin.add_ws_route(ws_route, is_legacy)
                return

    @property
    def device_commands(self) -> List[str]:
        return list(
            itertools.chain.from_iterable(
                plugin.device_commands for plugin in bluetooth_plugins
            )
        ) + ["getConnInfo"]

    @property
    def adapter_commands(self) -> List[str]:
        return list(
            itertools.chain.from_iterable(
                plugin.adapter_commands for plugin in bluetooth_plugins
            )
        )

    @property
    def controller_addresses(self) -> Dict[str, str]:
        return self._controller_addresses

    async def get_remapped_controller(self, controller_friendly_name: str):
        """Scan present controllers and find the controller with address associated with
        controller_friendly_name, in _controller_addresses dictionary.
        This allows for consistent referencing of controller by REST API name in the event
        the controller bluez object path changes in the system. (e.g. /org/bluez/hci5)
        """
        if controller_friendly_name not in self._controller_addresses.keys():
            return None
        address = self._controller_addresses[controller_friendly_name]
        bus = await DBusManager().get_bus()
        remote_om = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
        ).get_interface(DBUS_OM_IFACE)
        objects = await remote_om.call_get_managed_objects()

        for controller, props in objects.items():
            if GATT_MANAGER_IFACE in props.keys():
                if (
                    ADAPTER_IFACE in props.keys()
                    and "Address" in props[ADAPTER_IFACE].keys()
                ):
                    if address == variant_to_python(props[ADAPTER_IFACE]["Address"]):
                        return controller
        return None

    async def remapped_controller_to_friendly_name(self, controller: str) -> str:
        """Lookup the REST API name of the controller with the address matching the provided
        controller by dbus path.
        """
        bus = await DBusManager().get_bus()
        controller_obj = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            controller,
            await bus.introspect(BLUEZ_SERVICE_NAME, controller),
        )

        if not controller_obj:
            return ""
        adapter_interface = controller_obj.get_interface(ADAPTER_IFACE)
        requested_address = variant_to_python(await adapter_interface.get_address())
        for controller_friendly_name, address in self._controller_addresses.items():
            if requested_address == address:
                return controller_friendly_name
        return ""

    async def discover_controllers(self, renumber=True):
        """
        Find objects that have the bluez service and a GattManager1 interface,
        building _controller_addresses dictionary to later allow referencing of
        controllers by fixed name, even if their dbus object path changes.
        The assumption is that all controllers will be present in the system
        with the names the REST API wants to expose them under when Summit RCM starts,
        and that Summit RCM will never restart.
        If these assumptions are not true, renumber can be set to simply number
        discovered controllers as controller0 and up.
        """
        bus = await DBusManager().get_bus()
        remote_om = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
        ).get_interface(DBUS_OM_IFACE)
        objects = await remote_om.call_get_managed_objects()
        controller_number = len(self._controller_addresses.keys())

        for controller, props in objects.items():
            if GATT_MANAGER_IFACE in props.keys():
                if renumber:
                    controller_friendly_name: str = f"controller{controller_number}"
                else:
                    controller_friendly_name: str = controller_pretty_name(controller)
                if (
                    ADAPTER_IFACE in props.keys()
                    and "Address" in props[ADAPTER_IFACE].keys()
                ):
                    address = variant_to_python(props[ADAPTER_IFACE]["Address"])
                    if address not in self._controller_addresses.values():
                        self._controller_addresses[controller_friendly_name] = address
                        syslog(
                            LOG_INFO,
                            f"assigning controller {controller} at address {address} "
                            f"to REST API name {controller_friendly_name}",
                        )
                        controller_number += 1

    async def register_controller_callbacks(self):
        if not self._controller_callbacks_registered:
            try:
                self._controller_callbacks_registered = True

                bus = await DBusManager().get_bus()
                interface = bus.get_proxy_object(
                    BLUEZ_SERVICE_NAME,
                    "/",
                    await bus.introspect(BLUEZ_SERVICE_NAME, "/"),
                ).get_interface(DBUS_OM_IFACE)
                interface.on_interfaces_removed(self.interface_removed_cb)
                interface.on_interfaces_added(self.interface_added_cb)
            except Exception as exception:
                self.log_exception(exception)

    async def interface_added_cb(self, interface: str, *args):
        try:
            if ADAPTER_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth interface added: {str(interface)}")
                # IF bluetoothd crashed, may want to AgentSingleton.clear_instance()
                # For now, assume the controller was previously removed and has been re-attached.
                await self.controller_restore(interface)
            elif DEVICE_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth device added: {str(interface)}")
                await self.device_restore(interface)
        except Exception as exception:
            self.log_exception(exception)

    def log_exception(self, exception, message: str = ""):
        self._logger.exception(exception)
        syslog(LOG_ERR, message + str(exception))

    async def interface_removed_cb(self, interface: str, *args):
        try:
            if ADAPTER_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth interface removed: {str(interface)}")
                _, adapter_obj, _ = await get_controller_obj(interface)
                for plugin in bluetooth_plugins:
                    try:
                        await plugin.ControllerRemovedNotify(interface, adapter_obj)
                    except Exception as exception:
                        self.log_exception(exception)
        except Exception as exception:
            self.log_exception(exception)

    async def controller_restore(self, controller: str = "/org/bluez/hci0"):
        """
        :param controller: controller whose state will be restored
        :return: None

        Call when the specified controller experienced a HW reset, for example, in case
        of a HW malfunction, or system power-save sleep.
        Attempts to re-establish previously commanded controller state.
        * Note the assumption is that this LCM process was used to establish controller state -
        assumption unsatisfied if prior run of LCM or another tool was used to alter controller
        state.
        """
        # we remove the bus path by convention, so the index names match that used by hosts
        # in REST API
        controller_friendly_name: str = await self.remapped_controller_to_friendly_name(
            controller
        )
        syslog(
            LOG_INFO,
            f"controller_restore: restoring controller state for REST API name "
            f"{controller_friendly_name}",
        )
        controller_state = self.get_controller_state(controller_friendly_name)

        _, adapter_obj, _ = await get_controller_obj(controller)

        if not adapter_obj:
            syslog(
                LOG_ERR,
                f"Reset notification received for controller {controller}, "
                "but adapter_obj not found",
            )
            return

        # First, set controller properties, powering it on if previously powered.
        adapter_interface = adapter_obj.get_interface(ADAPTER_IFACE)
        try:
            await self.set_adapter_properties(
                adapter_interface,
                controller,
                controller_state.properties,
            )
        except Exception as exception:
            self.log_exception(exception)

        # Second, schedule set of each device's properties.
        for device_uuid, _ in controller_state.device_properties_uuids.items():
            self._devices_to_restore.update({device_uuid: None})

    async def device_restore(self, device: str):
        """Set device's properties, and plugin protocol connections if applicable."""
        bus, device_obj, _ = await get_controller_obj(device)

        if not device_obj:
            syslog(
                LOG_ERR,
                f"Reset notification received for device {device}, "
                "but device_obj not found",
            )
            return
        device_interface = device_obj.get_interface(DEVICE_IFACE)
        device_uuid = uri_to_uuid(
            variant_to_python(await device_interface.get_address())
        )

        if device_uuid not in self._devices_to_restore.keys():
            return

        self._devices_to_restore.pop(device_uuid)

        match = DEVICE_ADAPTER_GROUP_PATTERN.match(device)
        if not match or match.lastindex < 1:
            syslog(
                LOG_ERR,
                f"device_restore couldn't determine controller of device {device}",
            )
            return
        controller = match[1]
        controller_friendly_name: str = await self.remapped_controller_to_friendly_name(
            controller
        )
        syslog(
            LOG_INFO,
            f"device_restore: restoring device state for {device} on controller "
            f"REST API name {controller_friendly_name}",
        )
        controller_state = self.get_controller_state(controller_friendly_name)
        bus, adapter_obj, _ = await get_controller_obj(controller)
        adapter_interface = adapter_obj.get_interface(ADAPTER_IFACE)

        cached_device_properties = self.get_device_properties(
            controller_state, device_uuid
        )
        device, _ = await find_device(bus, device_uuid)
        if device is not None:
            device_obj = bus.get_proxy_object(
                BLUEZ_SERVICE_NAME,
                device,
                await bus.introspect(BLUEZ_SERVICE_NAME, device),
            )
            device_interface = device_obj.get_interface(DEVICE_IFACE)
            try:
                await self.set_device_properties(
                    adapter_interface,
                    device_interface,
                    device_uuid,
                    cached_device_properties,
                )
            except Exception as exception:
                self.log_exception(exception, "failed setting device properties: ")
        else:
            syslog(
                LOG_ERR, f"***couldn't find device {device_uuid} to restore properties"
            )

        # Notify plugins, re-establishing protocol links.
        # We do not wait for BT connections to restore, so service discovery may not be complete
        # when plugins receive notification.
        for plugin in bluetooth_plugins:
            try:
                await plugin.DeviceAddedNotify(device, device_uuid, device_obj)
            except Exception as exception:
                self.log_exception(exception)

    async def get_device_property(
        self, obj_path: str, interface: str, property_name: str
    ) -> Any:
        """Get the specified interface property for the object at the given path."""
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=BLUEZ_SERVICE_NAME,
                path=obj_path,
                interface=DBUS_PROP_IFACE,
                member="Get",
                signature="ss",
                body=[interface, property_name],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        return variant_to_python(reply.body[0])

    async def set_device_property(
        self,
        obj_path: str,
        interface: str,
        property_name: str,
        value: Any,
        value_signature: str,
    ) -> None:
        """
        Set the specified interface property for the object at the given path to the defined value
        using the provided signature.
        """
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=BLUEZ_SERVICE_NAME,
                path=obj_path,
                interface=DBUS_PROP_IFACE,
                member="Set",
                signature="ssv",
                body=[interface, property_name, Variant(value_signature, value)],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    def get_controller_state(
        self, controller_friendly_name: str
    ) -> BluetoothControllerState:
        controller_friendly_name = controller_pretty_name(controller_friendly_name)
        if controller_friendly_name not in self._controller_states:
            self._controller_states[
                controller_friendly_name
            ] = BluetoothControllerState()
        return self._controller_states[controller_friendly_name]

    def get_device_properties(
        self, controller_state: BluetoothControllerState, device_uuid: str
    ):
        """
        :param controller_state: controller device is on
        :param device_uuid: see uri_to_uuid()
        :return: dictionary map of device property names and values
        """
        if device_uuid not in controller_state.device_properties_uuids:
            controller_state.device_properties_uuids[device_uuid] = {}
        return controller_state.device_properties_uuids[device_uuid]

    @staticmethod
    def result_parameter_not_one_of(parameter: str, not_one_of):
        return {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied {parameter} parameter must be one of {not_one_of}",
        }

    async def set_adapter_properties(
        self,
        adapter_interface: ProxyInterface,
        controller_friendly_name,
        post_data,
    ):
        """Set properties on an adapter (controller)"""
        result = {}
        powered = post_data.get("powered", None)
        discovering = post_data.get("discovering", None)
        discoverable = post_data.get("discoverable", None)
        transport_filter = post_data.get("transportFilter", None)
        if powered is not None:
            await adapter_interface.set_powered(bool(powered))
            if not powered:
                # Do not attempt to set discoverable or discovering state if powering off
                discoverable = discoverable if discoverable else None
                discovering = discovering if discovering else None

        if transport_filter is not None:
            result.update(
                await self.set_adapter_transport_filter(
                    adapter_interface, controller_friendly_name, transport_filter
                )
            )
            if (
                "SDCERR" in result
                and result["SDCERR"] != definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            ):
                return result
        if discoverable is not None:
            await adapter_interface.set_discoverable(bool(discoverable))
        if discovering is not None:
            discovering_state = variant_to_python(
                await adapter_interface.get_discovering()
            )
            if discovering_state != discovering:
                if discovering:
                    await adapter_interface.call_start_discovery()
                else:
                    await adapter_interface.call_stop_discovery()

        if "SDCERR" not in result:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        return result

    def get_adapter_transport_filter(self, controller_friendly_name):
        controller_state = self.get_controller_state(controller_friendly_name)
        return controller_state.properties.get("transportFilter", None)

    async def set_adapter_transport_filter(
        self,
        adapter_interface: ProxyInterface,
        controller_friendly_name,
        transport_filter,
    ):
        """Set a transport filter on the controller.  Note that "When multiple clients call
        SetDiscoveryFilter, their filters are internally merged" """
        result = {}
        discovery_filters = {"Transport": Variant("s", str(transport_filter))}
        try:
            await adapter_interface.call_set_discovery_filter(discovery_filters)
        except Exception:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = f"Transport filter {transport_filter} not accepted"
            return result

        controller_state = self.get_controller_state(controller_friendly_name)
        controller_state.properties["transportFilter"] = transport_filter
        return result

    async def set_device_properties(
        self,
        adapter_interface: ProxyInterface,
        device_interface: ProxyInterface,
        device_uuid: str,
        post_data,
    ):
        result = {}
        for settable_property in SETTABLE_DEVICE_PROPS:
            prop_name, prop_type, prop_signature = settable_property
            value = post_data.get(lower_camel_case(prop_name), None)
            if value is not None:
                await self.set_device_property(
                    obj_path=device_interface.path,
                    interface=DEVICE_IFACE,
                    property_name=prop_name,
                    value=prop_type(value),
                    value_signature=prop_signature,
                )
        auto_connect = post_data.get("autoConnect", None)
        if auto_connect == 1:
            await create_agent_singleton()
        paired = post_data.get("paired", None)
        if paired == 1:
            paired_state = (
                1 if variant_to_python(await device_interface.get_paired()) else 0
            )
            if paired_state != paired:
                await create_agent_singleton()
                await asyncio.wait_for(
                    device_interface.call_pair(), PAIR_TIMEOUT_SECONDS
                )
        elif paired == 0:
            await self.remove_device_method(adapter_interface, device_interface)
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            return result
        connected = post_data.get("connected", None)
        connected_state = (
            1 if variant_to_python(await device_interface.get_connected()) else 0
        )
        if connected_state != connected:
            if connected == 1:
                # Note - device may need to be paired prior to connecting
                # AgentSingleton can be registered to allow BlueZ to auto-pair (without bonding)
                await create_agent_singleton()
                if bluetooth_ble_plugin:
                    await bluetooth_ble_plugin.initialize()
                if bluetooth_ble_plugin and bluetooth_ble_plugin.bt:
                    # Use ig BLE plugin if available, because it will refuse to
                    # interact with devices it has not explicitly connected to.
                    # Pass device path to ig BLE plugin, as it will fail
                    # to connect to devices it has not previously "discovered".
                    await bluetooth_ble_plugin.bt.connect(
                        device_uuid, device_interface.path
                    )
                else:
                    await asyncio.wait_for(
                        device_interface.call_connect(), CONNECT_TIMEOUT_SECONDS
                    )
            elif connected == 0:
                await device_interface.call_disconnect()
        passkey = post_data.get("passkey", None)
        if passkey is not None:
            agent_instance = await AgentSingleton.get_instance()
            if agent_instance:
                agent_instance.passkeys[device_interface.path] = passkey
        # Found device, set any requested properties.  Assume success.
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        return result

    async def remove_device_method(
        self, adapter_interface: ProxyInterface, device_interface: ProxyInterface
    ):
        device_connected = variant_to_python(await device_interface.get_connected())
        if device_connected:
            await device_interface.call_disconnect()
        device_address = variant_to_python(await device_interface.get_address())
        await adapter_interface.call_remove_device(device_interface.path)
        # If RemoveDevice is successful, further work on device will not be possible.
        device_uuid = uri_to_uuid(device_address)
        for plugin in bluetooth_plugins:
            try:
                await plugin.DeviceRemovedNotify(device_uuid, device_interface)
            except Exception as exception:
                self.log_exception(exception)

    async def execute_device_command(
        self,
        bus,
        command,
        device_uuid: str,
        device_interface: Optional[ProxyInterface],
        adapter_interface: Optional[ProxyInterface],
        post_data: Optional[dict] = None,
    ):
        result = {}
        error_message = None
        processed = False
        if command == "getConnInfo":
            processed = True

            try:
                reply = await bus.call(
                    Message(
                        destination=BLUEZ_SERVICE_NAME,
                        path=device_interface.path,
                        interface=DEVICE_IFACE,
                        member="GetConnInfo",
                    )
                )

                if reply.message_type == MessageType.ERROR:
                    raise Exception(reply.body[0])

                result["rssi"] = reply.body[0]
                result["tx_power"] = reply.body[1]
                result["max_tx_power"] = reply.body[2]
            except Exception as exception:
                self.log_exception(exception)
                error_message = "Unable to get connection info"
        else:
            for plugin in bluetooth_plugins:
                try:
                    processed, error_message = await plugin.ProcessDeviceCommand(
                        bus,
                        command,
                        device_uuid,
                        device_interface,
                        adapter_interface,
                        post_data,
                        self.remove_device_method,
                    )
                except Exception as exception:
                    self.log_exception(exception)
                    processed = True
                    error_message = f"Command {command} failed with {str(exception)}"
                    break
                if processed:
                    break

        if not processed:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = f"Unrecognized command {command}"
        elif error_message:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = error_message
        else:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = ""

        return result

    async def execute_adapter_command(
        self,
        bus,
        command,
        controller_friendly_name: str,
        adapter_interface: Optional[ProxyInterface],
        post_data: Optional[dict] = None,
    ):
        result = {}
        error_message = None
        processed = False
        for plugin in bluetooth_plugins:
            try:
                (
                    processed,
                    error_message,
                    process_result,
                ) = await plugin.ProcessAdapterCommand(
                    bus, command, controller_friendly_name, adapter_interface, post_data
                )
                if process_result:
                    result.update(process_result)
            except Exception as exception:
                self.log_exception(exception)
                processed = True
                error_message = f"Command {command} failed with {str(exception)}"
                break
            if processed:
                break

        if not processed:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = f"Unrecognized command {command}"
        elif error_message:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = error_message
        else:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = ""

        return result
