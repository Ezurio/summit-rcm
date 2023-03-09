import itertools
import logging
import os
import re
from syslog import syslog, LOG_ERR, LOG_INFO
from typing import Optional, List, Dict

import falcon

from ..dbus_manager import DBusManager

from ..settings import SystemSettingsManage
from subprocess import run, TimeoutExpired

from . import bt_plugin
from .. import definition
from .ble import (
    controller_pretty_name,
    find_device,
    find_devices,
    DEVICE_IFACE,
    ADAPTER_IFACE,
    DBUS_OM_IFACE,
    AgentSingleton,
    BLUEZ_SERVICE_NAME,
    uri_to_uuid,
    GATT_MANAGER_IFACE,
)
from .bt_controller_state import BluetoothControllerState

# TODO: USER_PERMISSION_TYPES for Bluetooth

PAIR_TIMEOUT_SECONDS = 60
CONNECT_TIMEOUT_SECONDS = 60

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [
    ("Trusted", bool),
    ("AutoConnect", bool),
    ("AutoConnectAutoDisable", bool),
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
    from ..hid.barcode_scanner import HidBarcodeScannerPlugin

    bluetooth_plugins.append(HidBarcodeScannerPlugin())
    syslog("bluetooth: HidBarcodeScannerPlugin loaded")
except ImportError:
    syslog("bluetooth: HidBarcodeScannerPlugin NOT loaded")

try:
    from ..vsp.vsp_connection import VspConnectionPlugin

    bluetooth_plugins.append(VspConnectionPlugin())
    syslog("bluetooth: VspConnectionPlugin loaded")
except ImportError:
    syslog("bluetooth: VspConnectionPlugin NOT loaded")

try:
    bluetooth_ble_plugin = None
    from .bt_ble import BluetoothBlePlugin

    bluetooth_ble_plugin = BluetoothBlePlugin()
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


class Bluetooth:
    def __init__(self):
        self._controller_states: Dict[str, BluetoothControllerState] = {}
        """ Controller state tracking - indexed by friendly (REST API) name
        """
        self._controller_addresses: Dict[str, str] = {}
        """ Controller addresses - indexed by friendly (REST API) name
        """
        self._controller_callbacks_registered = False
        self._logger = logging.getLogger(__name__)
        self._devices_to_restore: Dict[str, type(None)] = {}
        """ Map of device uuids to restore state due to associated controller reset
        """

    async def setup(self) -> None:
        """
        Run async logic required to setup Bluetooth intergration
        """
        await self.discover_controllers()

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

    @staticmethod
    def get_bluez_version() -> str:
        """
        Retrieve the current version of BlueZ as a string by running 'bluetoothctl --version'
        """
        BLUEZ_VERSION_RE = r"bluetoothctl: (?P<VERSION>.*)"
        BLUETOOTHCTL_PATH = "/usr/bin/bluetoothctl"

        if not os.path.exists(BLUETOOTHCTL_PATH):
            return "Unknown"

        try:
            proc = run(
                [BLUETOOTHCTL_PATH, "--version"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                for line in proc.stdout.decode("utf-8").splitlines():
                    line = line.strip()
                    match = re.match(BLUEZ_VERSION_RE, line)
                    if match:
                        return str(match.group("VERSION"))
        except TimeoutExpired:
            syslog(LOG_ERR, "Call to 'bluetoothctl --version' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call to 'bluetoothctl --version' failed: {str(e)}")

        return "Unknown"

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
                    if address == props[ADAPTER_IFACE]["Address"]:
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
        adapter_props = controller_obj.get_interface("org.freedesktop.DBus.Properties")
        requested_address = await adapter_props.call_get(ADAPTER_IFACE, "Address")
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
                    address = props[ADAPTER_IFACE]["Address"]
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
            self._controller_callbacks_registered = True

            bus = await DBusManager().get_bus()
            interface = bus.get_proxy_object(
                DBUS_OM_IFACE, "/", await bus.introspect(DBUS_OM_IFACE, "/")
            ).get_interface(DBUS_OM_IFACE)
            interface.on_interfaces_removed(self.interface_removed_cb)
            interface.on_interfaces_added(self.interface_added_cb)

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
        except Exception as e:
            self.log_exception(e)

    def log_exception(self, e, message: str = ""):
        self._logger.exception(e)
        syslog(LOG_ERR, message + str(e))

    async def interface_removed_cb(self, interface: str, *args):
        try:
            if ADAPTER_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth interface removed: {str(interface)}")
                bus, adapter_obj, get_controller_result = await get_controller_obj(
                    interface
                )
                for plugin in bluetooth_plugins:
                    try:
                        plugin.ControllerRemovedNotify(interface, adapter_obj)
                    except Exception as e:
                        self.log_exception(e)
        except Exception as e:
            self.log_exception(e)

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

        bus, adapter_obj, get_controller_result = await get_controller_obj(controller)

        if not adapter_obj:
            syslog(
                LOG_ERR,
                f"Reset notification received for controller {controller}, "
                "but adapter_obj not found",
            )
            return

        # First, set controller properties, powering it on if previously powered.
        adapter_props = adapter_obj.get_interface("org.freedesktop.DBus.Properties")
        adapter_methods = adapter_obj.get_interface("org.freedesktop.DBus.Methods")
        try:
            self.set_adapter_properties(
                adapter_methods,
                adapter_props,
                controller,
                controller_state.properties,
            )
        except Exception as e:
            self.log_exception(e)

        # Second, schedule set of each device's properties.
        for device_uuid, properties in controller_state.device_properties_uuids.items():
            self._devices_to_restore.update({device_uuid: None})

    async def device_restore(self, device: str):
        """Set device's properties, and plugin protocol connections if applicable."""
        bus, device_obj, get_controller_result = await get_controller_obj(device)

        if not device_obj:
            syslog(
                LOG_ERR,
                f"Reset notification received for device {device}, "
                "but device_obj not found",
            )
            return

        device_props = device_obj.get_interface("org.freedesktop.DBus.Properties")

        device_address = await device_props.call_get(DEVICE_IFACE, "Address")
        device_uuid = uri_to_uuid(device_address)

        if device_uuid not in self._devices_to_restore.keys():
            return

        self._devices_to_restore.pop(device_uuid)

        m = DEVICE_ADAPTER_GROUP_PATTERN.match(device)
        if not m or m.lastindex < 1:
            syslog(
                LOG_ERR,
                f"device_restore couldn't determine controller of device {device}",
            )
            return
        controller = m[1]
        controller_friendly_name: str = await self.remapped_controller_to_friendly_name(
            controller
        )
        syslog(
            LOG_INFO,
            f"device_restore: restoring device state for {device} on controller "
            f"REST API name {controller_friendly_name}",
        )
        controller_state = self.get_controller_state(controller_friendly_name)
        bus, adapter_obj, get_controller_result = await get_controller_obj(controller)
        adapter_methods = adapter_obj.get_interface("org.freedesktop.DBus.Methods")

        cached_device_properties = self.get_device_properties(
            controller_state, device_uuid
        )
        device, device_props = find_device(bus, device_uuid)
        if device is not None:
            device_obj = bus.get_proxy_object(
                BLUEZ_SERVICE_NAME,
                device,
                await bus.introspect(BLUEZ_SERVICE_NAME, device),
            )
            device_methods = device_obj.get_interface("org.freedesktop.DBus.Methods")
            device_properties = device_obj.get_interface(
                "org.freedesktop.DBus.Properties"
            )
            try:
                self.set_device_properties(
                    adapter_obj,
                    adapter_methods,
                    device_obj,
                    device_methods,
                    device_properties,
                    device_uuid,
                    cached_device_properties,
                )
            except Exception as e:
                self.log_exception(e, "failed setting device properties: ")
        else:
            syslog(
                LOG_ERR, f"***couldn't find device {device_uuid} to restore properties"
            )

        # Notify plugins, re-establishing protocol links.
        # We do not wait for BT connections to restore, so service discovery may not be complete
        # when plugins receive notification.
        for plugin in bluetooth_plugins:
            try:
                plugin.DeviceAddedNotify(device, device_uuid, device_obj)
            except Exception as e:
                self.log_exception(e)

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            filters: Optional[List[str]] = None
            if "filter" in req.params:
                filters = req.params["filter"].split(",")

            if "controller" in req.params:
                controller_friendly_name: str = controller_pretty_name(
                    req.params["controller"]
                )
            else:
                controller_friendly_name: str = ""

            if "device" in req.params:
                device_uuid = uri_to_uuid(req.params["device"])
            else:
                device_uuid = None

            # get the system bus
            bus = await DBusManager().get_bus()
            # get the ble controller
            if controller_friendly_name:
                controller = (
                    controller_friendly_name,
                    await self.get_remapped_controller(controller_friendly_name),
                )
                controllers = [controller]
                if not controller[1]:
                    result[
                        "InfoMsg"
                    ] = f"Controller {controller_friendly_name} not found."
                    resp.media = result
                    return
            else:
                controllers = {
                    (x, await self.get_remapped_controller(x))
                    for x in self._controller_addresses.keys()
                }

            for controller_friendly_name, controller in controllers:
                controller_result = {}
                controller_obj = bus.get_proxy_object(
                    BLUEZ_SERVICE_NAME,
                    controller,
                    await bus.introspect(BLUEZ_SERVICE_NAME, controller),
                )

                if not controller_obj:
                    result[
                        "InfoMsg"
                    ] = f"Controller {controller_friendly_name} not found."
                    resp.media = result
                    return

                matched_filter = False
                if not device_uuid:
                    if not filters or "bluetoothDevices" in filters:
                        controller_result["bluetoothDevices"] = find_devices(bus)
                        matched_filter = True

                    adapter_props = controller_obj.get_interface(
                        "org.freedesktop.DBus.Properties"
                    )

                    if not filters or "transportFilter" in filters:
                        controller_result[
                            "transportFilter"
                        ] = self.get_adapter_transport_filter(controller_friendly_name)
                        matched_filter = True

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or lower_camel_case(pass_property) in filters:
                            controller_result[
                                lower_camel_case(pass_property)
                            ] = await adapter_props.call_get(
                                ADAPTER_IFACE, pass_property
                            )
                            matched_filter = True

                    result[controller_friendly_name] = controller_result
                    if filters and not matched_filter:
                        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                        result["InfoMsg"] = f"filters {filters} not matched"
                        resp.media = result
                        return
                else:
                    result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                    device, device_props = find_device(bus, device_uuid)
                    if not device:
                        result["InfoMsg"] = "Device not found"
                        resp.media = result
                        return
                    result.update(device_props)
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        await self.register_controller_callbacks()

        if "controller" in req.params:
            controller_friendly_name = controller_pretty_name(req.params["controller"])
        else:
            controller_friendly_name = "controller0"

        controller = await self.get_remapped_controller(controller_friendly_name)

        if "device" in req.params:
            device_uuid = uri_to_uuid(req.params["device"])
        else:
            device_uuid = None

        post_data = await req.get_media()
        bus, adapter_obj, get_controller_result = await get_controller_obj(controller)

        result.update(get_controller_result)

        if not adapter_obj:
            resp.media = result
            return

        controller_state = self.get_controller_state(controller_friendly_name)

        try:
            adapter_props = adapter_obj.get_interface("org.freedesktop.DBus.Properties")
            adapter_methods = adapter_obj.get_interface("org.freedesktop.DBus.Methods")

            command = post_data["command"] if "command" in post_data else None
            if not device_uuid:
                # adapter-specific operation
                if command:
                    if command not in self.adapter_commands:
                        result.update(
                            self.result_parameter_not_one_of(
                                "command", self.adapter_commands
                            )
                        )
                    else:
                        result.update(
                            self.execute_adapter_command(
                                bus, command, controller_friendly_name, adapter_obj
                            )
                        )
                    return result
                else:
                    for prop in CACHED_ADAPTER_PROPS:
                        if prop in post_data:
                            controller_state.properties[prop] = post_data.get(prop)
                    result.update(
                        self.set_adapter_properties(
                            adapter_methods,
                            adapter_props,
                            controller_friendly_name,
                            post_data,
                        )
                    )
            else:
                # device-specific operation
                if command and command not in self.device_commands:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", self.device_commands
                        )
                    )
                    return result
                device, device_props = find_device(bus, device_uuid)
                if device is None:
                    result["InfoMsg"] = "Device not found"
                    if command:
                        # Forward device-specific commands on to plugins even if device
                        # is not found:
                        result.update(
                            self.execute_device_command(
                                bus, command, device_uuid, None, None
                            )
                        )
                    return result

                device_obj = bus.get_proxy_object(
                    BLUEZ_SERVICE_NAME,
                    device,
                    await bus.introspect(BLUEZ_SERVICE_NAME, device),
                )

                device_methods = dbus.Interface(
                    device_obj, "org.freedesktop.DBus.Methods"
                )
                device_properties = dbus.Interface(
                    device_obj, "org.freedesktop.DBus.Properties"
                )

                if command:
                    result.update(
                        self.execute_device_command(
                            bus, command, device_uuid, device, adapter_obj
                        )
                    )
                    return result
                else:
                    cached_device_properties = self.get_device_properties(
                        controller_state, device_uuid
                    )
                    for prop in CACHED_DEVICE_PROPS:
                        if prop in post_data:
                            cached_device_properties[prop] = post_data.get(prop)
                    result.update(
                        self.set_device_properties(
                            adapter_obj,
                            adapter_methods,
                            device_obj,
                            device_methods,
                            device_properties,
                            device_uuid,
                            post_data,
                        )
                    )

        except Exception as e:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        return result

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

    def set_adapter_properties(
        self, adapter_methods, adapter_props, controller_friendly_name, post_data
    ):
        """Set properties on an adapter (controller)"""
        result = {}
        powered = post_data.get("powered", None)
        discovering = post_data.get("discovering", None)
        discoverable = post_data.get("discoverable", None)
        transport_filter = post_data.get("transportFilter", None)
        if powered is not None:
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(powered))
            if not powered:
                # Do not attempt to set discoverable or discovering state if powering off
                discoverable = discoverable if discoverable else None
                discovering = discovering if discovering else None

        if transport_filter is not None:
            result.update(
                self.set_adapter_transport_filter(
                    adapter_methods, controller_friendly_name, transport_filter
                )
            )
            if (
                "SDCERR" in result
                and result["SDCERR"] != definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            ):
                return result
        if discoverable is not None:
            adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(discoverable))
        if discovering is not None:
            discovering_state = adapter_props.Get(ADAPTER_IFACE, "Discovering")
            if discovering_state != discovering:
                if discovering:
                    adapter_methods.get_dbus_method("StartDiscovery", ADAPTER_IFACE)()
                else:
                    adapter_methods.get_dbus_method("StopDiscovery", ADAPTER_IFACE)()

        if "SDCERR" not in result:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        return result

    def get_adapter_transport_filter(self, controller_friendly_name):
        controller_state = self.get_controller_state(controller_friendly_name)
        return controller_state.properties.get("transportFilter", None)

    def set_adapter_transport_filter(
        self, adapter_methods, controller_friendly_name, transport_filter
    ):
        """Set a transport filter on the controller.  Note that "When multiple clients call
        SetDiscoveryFilter, their filters are internally merged" """
        result = {}
        discovery_filters = {"Transport": transport_filter}
        discovery_filters_dbus = python_to_dbus(discovery_filters)
        try:
            adapter_methods.get_dbus_method("SetDiscoveryFilter", ADAPTER_IFACE)(
                discovery_filters_dbus
            )
        except dbus.DBusException:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = f"Transport filter {transport_filter} not accepted"
            return result

        controller_state = self.get_controller_state(controller_friendly_name)
        controller_state.properties["transportFilter"] = transport_filter
        return result

    def set_device_properties(
        self,
        adapter_obj,
        adapter_methods,
        device_obj: dbus.ObjectPath,
        device_methods,
        device_properties,
        device_uuid: str,
        post_data,
    ):
        result = {}
        for settable_property in SETTABLE_DEVICE_PROPS:
            prop_name, prop_type = settable_property
            value = post_data.get(lower_camel_case(prop_name), None)
            if value is not None:
                device_properties.Set(
                    DEVICE_IFACE, prop_name, python_to_dbus(value, prop_type)
                )
        paired = post_data.get("paired", None)
        if paired == 1:
            paired_state = device_properties.Get(DEVICE_IFACE, "Paired")
            if paired_state != paired:
                AgentSingleton()
                bus = dbus.SystemBus()
                bus.call_blocking(
                    bus_name=BLUEZ_SERVICE_NAME,
                    object_path=device_obj.object_path,
                    dbus_interface=DEVICE_IFACE,
                    method="Pair",
                    signature="",
                    args=[],
                    timeout=PAIR_TIMEOUT_SECONDS,
                )
        elif paired == 0:
            self.remove_device_method(adapter_obj, device_obj.object_path)
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            return result
        connected = post_data.get("connected", None)
        connected_state = device_properties.Get(DEVICE_IFACE, "Connected")
        if connected_state != connected:
            if connected == 1:
                # Note - device may need to be paired prior to connecting
                # AgentSingleton can be registered to allow BlueZ to auto-pair (without bonding)
                AgentSingleton()
                if bluetooth_ble_plugin:
                    bluetooth_ble_plugin.initialize()
                if bluetooth_ble_plugin and bluetooth_ble_plugin.bt:
                    # Use ig BLE plugin if available, because it will refuse to
                    # interact with devices it has not explicitly connected to.
                    # Pass device path to ig BLE plugin, as it will fail
                    # to connect to devices it has not previously "discovered".
                    bluetooth_ble_plugin.bt.connect(device_uuid, device_obj.object_path)
                else:
                    device_methods.get_dbus_method("Connect", DEVICE_IFACE)(
                        timeout=CONNECT_TIMEOUT_SECONDS
                    )
            elif connected == 0:
                device_methods.get_dbus_method("Disconnect", DEVICE_IFACE)()
        passkey = post_data.get("passkey", None)
        if passkey is not None:
            agent_instance = AgentSingleton.get_instance()
            if agent_instance:
                agent_instance.passkeys[device_obj.object_path] = passkey
        # Found device, set any requested properties.  Assume success.
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        return result

    def remove_device_method(self, adapter_obj, device):
        bus = dbus.SystemBus()
        device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
        device_methods = dbus.Interface(device_obj, "org.freedesktop.DBus.Methods")
        device_properties = dbus.Interface(
            device_obj, "org.freedesktop.DBus.Properties"
        )
        if device_properties.Get(DEVICE_IFACE, "Connected"):
            device_methods.get_dbus_method("Disconnect", DEVICE_IFACE)()
        adapter_methods = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Methods")
        device_address = device_properties.Get(DEVICE_IFACE, "Address")
        adapter_methods.get_dbus_method("RemoveDevice", ADAPTER_IFACE)(device_obj)
        # If RemoveDevice is successful, further work on device will not be possible.
        device_uuid = uri_to_uuid(device_address)
        for plugin in bluetooth_plugins:
            try:
                plugin.DeviceRemovedNotify(device_uuid, device_obj)
            except Exception as e:
                self.log_exception(e)

    def execute_device_command(
        self,
        bus,
        command,
        device_uuid: str,
        device: Optional[dbus.ObjectPath],
        adapter_obj: Optional[dbus.ObjectPath],
    ):
        result = {}
        error_message = None
        processed = False
        post_data = cherrypy.request.json
        if command == "getConnInfo":
            processed = True
            device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
            interface = dbus.Interface(device_obj, DEVICE_IFACE)
            (rssi, tx_power, max_tx_power) = interface.GetConnInfo()
            result["rssi"] = rssi
            result["tx_power"] = tx_power
            result["max_tx_power"] = max_tx_power
        else:
            for plugin in bluetooth_plugins:
                try:
                    processed, error_message = plugin.ProcessDeviceCommand(
                        bus,
                        command,
                        device_uuid,
                        device,
                        adapter_obj,
                        post_data,
                        self.remove_device_method,
                    )
                except Exception as e:
                    self.log_exception(e)
                    processed = True
                    error_message = f"Command {command} failed with {str(e)}"
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

    def execute_adapter_command(
        self,
        bus,
        command,
        controller_friendly_name: str,
        adapter_obj: dbus.ObjectPath,
    ):
        result = {}
        error_message = None
        processed = False
        post_data = cherrypy.request.json
        for plugin in bluetooth_plugins:
            try:
                processed, error_message, process_result = plugin.ProcessAdapterCommand(
                    bus, command, controller_friendly_name, adapter_obj, post_data
                )
                if process_result:
                    result.update(process_result)
            except Exception as e:
                self.log_exception(e)
                processed = True
                error_message = f"Command {command} failed with {str(e)}"
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
