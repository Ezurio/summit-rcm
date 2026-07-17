#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle BLE control.
"""

from enum import Enum
from syslog import syslog, LOG_ERR, LOG_WARNING
from typing import Tuple
from dbus_fast import DBusError, Variant
from dbus_fast.service import ServiceInterface, method
from summit_rcm.dbus_manager import DBusManager
from summit_rcm.utils import variant_to_python

DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
AGENT_IFACE = "org.bluez.Agent1"

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
BLUEZ_PATH_PREPEND = "/org/bluez/"
AGENT_PATH = "/com/summit/agent"
DEFAULT_PAIRING_IO_CAPABILITY = "NoInputNoOutput"


class BluetoothPairingIOCapability(str, Enum):
    """Enumeration of BlueZ pairing agent IO capabilities exposed over REST."""

    DISPLAY_ONLY = "DisplayOnly"
    DISPLAY_YES_NO = "DisplayYesNo"
    KEYBOARD_ONLY = "KeyboardOnly"
    KEYBOARD_DISPLAY = "KeyboardDisplay"
    NO_INPUT_NO_OUTPUT = "NoInputNoOutput"


def controller_pretty_name(name: str):
    """Return a name friendlier for REST API.
    controller0, controller1, etc., rather than /org/bluez/hci0, etc.
    """
    return name.replace("hci", "controller").replace("/org/bluez/", "")


def controller_bus_name(pretty_name: str):
    return pretty_name.replace("controller", "hci")


def uri_to_uuid(uri_uuid: str) -> str:
    """
    Standardize a device UUID (MAC address) from URI format (xx_xx_xx_xx_xx_xx) to conventional
    format (XX:XX:XX:XX:XX:XX)
    """
    return uri_uuid.upper().replace("_", ":")


async def find_controllers(bus):
    """
    Returns objects that have the bluez service and a GattManager1 interface
    """
    remote_om = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = await remote_om.call_get_managed_objects()

    controllers = []

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            controllers.append(o)

    return controllers


async def find_controller(bus, name: str = ""):
    """
    Returns the first object that has the bluez service and a GattManager1 interface and the
    provided name, if provided.
    """
    remote_om = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = await remote_om.call_get_managed_objects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            if not name:
                return o

            controller_name = o.replace(BLUEZ_PATH_PREPEND, "")
            if controller_name.lower() == name.lower():
                return o

    return None


def normalize_device_data(device_data: dict) -> dict:
    """Normalize the provided device property data for proper JSON formatting."""
    new_device_data = {}
    for prop_key, prop_value in device_data.items():
        if isinstance(prop_value, bool):
            new_device_data[prop_key] = 1 if prop_value else 0
            continue
        if prop_key in ["ManufacturerData" or "ServiceData"] and isinstance(
            prop_value, dict
        ):
            data_entry = {}
            for data_key, data_value in prop_value.items():
                data_entry[data_key] = list(bytes.fromhex(data_value))
            new_device_data[prop_key] = data_entry
            continue
        new_device_data[prop_key] = prop_value
    return new_device_data


async def find_devices(bus):
    """
    Returns the objects that have the bluez service and a DEVICE_IFACE interface
    """
    remote_om = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = await remote_om.call_get_managed_objects()

    devices = []

    for _, props in objects.items():
        if DEVICE_IFACE in props.keys():
            devices.append(
                normalize_device_data(variant_to_python(props[DEVICE_IFACE]))
            )

    return devices


async def find_device(bus, uuid) -> Tuple[str, dict]:
    """
    Returns the first object that has the bluez service and a DEVICE_IFACE interface.
    """
    remote_om = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, "/", await bus.introspect(BLUEZ_SERVICE_NAME, "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = await remote_om.call_get_managed_objects()

    for o, props in objects.items():
        if DEVICE_IFACE in props.keys():
            device = props[DEVICE_IFACE]
            if str(variant_to_python(device["Address"])).lower() == uuid.lower():
                return o, normalize_device_data(variant_to_python(props[DEVICE_IFACE]))

    return None, None


async def set_trusted(path):
    bus = await DBusManager().get_bus()
    props = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, path, await bus.introspect(BLUEZ_SERVICE_NAME, path)
    ).get_interface(DBUS_PROP_IFACE)
    await props.call_set(DEVICE_IFACE, "Trusted", Variant("b", True))


async def device_is_connected(bus, device):
    device_obj = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, device, await bus.introspect(BLUEZ_SERVICE_NAME, device)
    )
    device_interface = device_obj.get_interface(DEVICE_IFACE)
    connected_state = variant_to_python(await device_interface.get_connected())
    return connected_state


async def dev_connect(path):
    bus = await DBusManager().get_bus()
    dev = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, path, await bus.introspect(BLUEZ_SERVICE_NAME, path)
    ).get_interface(DEVICE_IFACE)
    await dev.call_connect()


class Rejected(DBusError):
    _dbus_error_name = "org.bluez.Error.Rejected"


class AgentSingleton:
    __instance = None

    @staticmethod
    async def get_instance():
        """Static access method."""
        if AgentSingleton.__instance is None:
            await create_agent_singleton()
        return AgentSingleton.__instance

    @staticmethod
    def clear_instance():
        AgentSingleton.__instance = None

    @staticmethod
    def get_existing_instance():
        return AgentSingleton.__instance

    def __init__(self):
        """Virtually private constructor."""
        self.passkeys = {}
        self.registered = False
        if AgentSingleton.__instance is None:
            AgentSingleton.__instance = self


async def unregister_agent_singleton() -> None:
    """Unregister and unexport the shared BlueZ agent if it is currently active."""

    bus = await DBusManager().get_bus()
    obj = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME,
        "/org/bluez",
        await bus.introspect(BLUEZ_SERVICE_NAME, "/org/bluez"),
    )
    agent_manager = obj.get_interface("org.bluez.AgentManager1")

    try:
        await agent_manager.call_unregister_agent(AGENT_PATH)
    except Exception:
        pass

    try:
        bus.unexport(AGENT_PATH)
    except Exception:
        pass

    agent_instance = AgentSingleton.get_existing_instance()
    if agent_instance is not None:
        agent_instance.registered = False


async def create_agent_singleton(
    io_capability: str = DEFAULT_PAIRING_IO_CAPABILITY,
) -> AgentSingleton:
    """
    Async wrapper to create/generate the AgentSingleton
    """

    requested_io_capability = io_capability or DEFAULT_PAIRING_IO_CAPABILITY
    agent_singleton = AgentSingleton.get_existing_instance() or AgentSingleton()
    current_io_capability = getattr(
        agent_singleton,
        "io_capability",
        DEFAULT_PAIRING_IO_CAPABILITY,
    )
    agent_singleton.io_capability = requested_io_capability

    if (
        agent_singleton.registered
        and current_io_capability == requested_io_capability
    ):
        return agent_singleton

    if agent_singleton.registered:
        syslog(
            "Re-registering agent for auto-pairing "
            f"with IO capability {requested_io_capability} "
            f"(was {current_io_capability})"
        )
        agent_singleton.registered = False
    else:
        syslog(
            "Registering agent for auto-pairing "
            f"with IO capability {requested_io_capability}"
        )

    try:
        # get the system bus
        bus = await DBusManager().get_bus()
        await unregister_agent_singleton()
        agent = AuthenticationAgent(AGENT_IFACE)
        bus.export(AGENT_PATH, agent)

        obj = bus.get_proxy_object(
            BLUEZ_SERVICE_NAME,
            "/org/bluez",
            await bus.introspect(BLUEZ_SERVICE_NAME, "/org/bluez"),
        )

        agent_manager = obj.get_interface("org.bluez.AgentManager1")
        await agent_manager.call_register_agent(AGENT_PATH, requested_io_capability)
        await agent_manager.call_request_default_agent(AGENT_PATH)
        agent_singleton.registered = True
    except Exception as exception:
        agent_singleton.registered = False
        syslog(LOG_ERR, str(exception))

    return agent_singleton


class AuthenticationAgent(ServiceInterface):
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @method()
    def Release(self):
        agent_instance = AgentSingleton.get_existing_instance()
        if agent_instance is not None:
            agent_instance.registered = False
        syslog("AuthenticationAgent Release")

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        syslog(f"AuthenticationAgent AuthorizeService ({str(device)}, {str(uuid)})")
        return

    @method()
    async def RequestPinCode(self, device: "o") -> "s":
        syslog(f"AuthenticationAgent RequestPinCode ({str(device)})")
        await set_trusted(device)
        return "000000"

    @method()
    async def RequestPasskey(self, device: "o") -> "u":
        syslog(f"AuthenticationAgent RequestPasskey ({str(device)})")
        await set_trusted(device)
        # passkey = ask("Enter passkey: ")
        # TODO: Implement with RESTful set
        passkey = 0
        agent_instance = await AgentSingleton.get_instance()
        if agent_instance:
            if device in agent_instance.passkeys:
                passkey = agent_instance.passkeys[device]
        return int(passkey)

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        syslog(
            f"AuthenticationAgent DisplayPasskey ({str(device)}, {passkey:06d} entered {entered:})"
        )

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        syslog(f"AuthenticationAgent DisplayPinCode ({str(device)}, {str(pincode)})")

    @method()
    async def RequestConfirmation(self, device: "o", passkey: "u"):
        syslog(
            f"AuthenticationAgent RequestConfirmation ({str(device)}, {passkey:06d})"
        )
        # The shared Bluetooth client path auto-accepts confirmation today. This
        # keeps pairing automation simple while still allowing peripherals with a
        # richer IO capability to surface their own approval workflows.
        try:
            await set_trusted(device)
        except Exception as exception:
            syslog(
                LOG_WARNING,
                f"Could not mark {str(device)} trusted during RequestConfirmation: {exception}",
            )
        return

    # Alcon Smart Remote utilizes RequestAuthorization
    # "used for requesting authorization for pairing requests which would otherwise not trigger any
    # action for the user The main situation where this would occur is an incoming SSP pairing
    # request that would trigger the just-works model."
    @method()
    def RequestAuthorization(self, device: "o"):
        syslog(f"AuthenticationAgent RequestAuthorization ({str(device)})")
        return

    @method()
    def Cancel(self):
        syslog("AuthenticationAgent Cancel")


class BLEWriteCharacteristicType(str, Enum):
    """
    Enumeration of valid Bluetooth GATT write characteristic types

    See below for more info:
    https://github.com/bluez/bluez/blob/master/doc/org.bluez.GattCharacteristic.rst#void-writevaluearraybyte-value-dict-options
    """

    BLE_CHR_WRITE_TYPE_DEFAULT = ""
    BLE_CHR_WRITE_TYPE_COMMAND = "command"
    BLE_CHR_WRITE_TYPE_REQUEST = "request"
    BLE_CHR_WRITE_TYPE_RELIABLE = "reliable"


class VSPSocketRxTypeEnum(str, Enum):
    """Enumeration of valid VSP socket Rx types"""

    BLE_VSP_SOCKET_RX_TYPE_RAW = "raw"
    BLE_VSP_SOCKET_RX_TYPE_JSON = "JSON"
