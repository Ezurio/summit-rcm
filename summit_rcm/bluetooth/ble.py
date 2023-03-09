from syslog import syslog, LOG_ERR
from typing import Tuple
from ..dbus_manager import DBusManager
from dbus_next import DBusError
from dbus_next.service import ServiceInterface, method

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
AGENT_PATH = "/com/lairdconnectivity/agent"


# def python_to_dbus(data, datatype=None):
#     # Convert python native data types to dbus data types
#     if not datatype:
#         datatype = type(data)

#     if datatype is bool or datatype is dbus.Boolean:
#         data = dbus.Boolean(data)
#     elif datatype is int or datatype is dbus.Int64:
#         data = dbus.Int64(data)
#     elif datatype is bytes or datatype is bytearray or datatype is dbus.ByteArray:
#         data = dbus.ByteArray(data)
#     elif isinstance(data, bytes):
#         data = [python_to_dbus(value) for value in data]
#     elif isinstance(data, bytearray):
#         data = [python_to_dbus(value) for value in data]
#     elif datatype is str:
#         data = dbus.String(data)
#     elif datatype is dict:
#         new_data = dbus.Dictionary()
#         for key in data.keys():
#             new_key = python_to_dbus(key)
#             new_data[new_key] = python_to_dbus(data[key])
#         data = new_data

#     return data


# def dbus_to_python_ex(data, datatype=None):
#     # Convert dbus data types to python native data types
#     if not datatype:
#         datatype = type(data)

#     if datatype is dbus.String:
#         data = str(data)
#     elif datatype is dbus.Boolean:
#         data = bool(data)
#     elif datatype is dbus.Int64:
#         data = int(data)
#     elif datatype is dbus.Byte:
#         data = int(data)
#     elif datatype is dbus.UInt32:
#         data = int(data)
#     elif datatype is dbus.Double:
#         data = float(data)
#     elif datatype is bytes or datatype is bytearray or datatype is dbus.ByteArray:
#         data = bytearray(data)
#     elif datatype is dbus.Array:
#         data = [dbus_to_python_ex(value) for value in data]
#     elif datatype is dbus.Dictionary:
#         new_data = dict()
#         for key in data.keys():
#             new_key = dbus_to_python_ex(key)
#             new_data[new_key] = dbus_to_python_ex(data[key])
#         data = new_data
#     return data


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


def find_controllers(bus):
    """
    Returns objects that have the bluez service and a GattManager1 interface
    """
    remote_om = bus.get_proxy_object(
        "BLUEZ_SERVICE_NAME", "/", bus.introspect_sync("BLUEZ_SERVICE_NAME", "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = remote_om.call_get_managed_objects_sync()

    controllers = []

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            controllers.append(o)

    return controllers


def find_controller(bus, name: str = ""):
    """
    Returns the first object that has the bluez service and a GattManager1 interface and the provided name, if provided.
    """
    remote_om = bus.get_proxy_object(
        "BLUEZ_SERVICE_NAME", "/", bus.introspect_sync("BLUEZ_SERVICE_NAME", "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = remote_om.call_get_managed_objects_sync()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            if not name:
                return o

            controller_name = o.replace(BLUEZ_PATH_PREPEND, "")
            if controller_name.lower() == name.lower():
                return o

    return None


def find_devices(bus):
    """
    Returns the objects that have the bluez service and a DEVICE_IFACE interface
    """
    remote_om = bus.get_proxy_object(
        "BLUEZ_SERVICE_NAME", "/", bus.introspect_sync("BLUEZ_SERVICE_NAME", "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = remote_om.call_get_managed_objects_sync()

    devices = []

    for o, props in objects.items():
        if DEVICE_IFACE in props.keys():
            devices.append(props[DEVICE_IFACE])

    return devices


def find_device(bus, uuid) -> Tuple[str, dict]:
    """
    Returns the first object that has the bluez service and a DEVICE_IFACE interface.
    """
    remote_om = bus.get_proxy_object(
        "BLUEZ_SERVICE_NAME", "/", bus.introspect_sync("BLUEZ_SERVICE_NAME", "/")
    ).get_interface(DBUS_OM_IFACE)
    objects = remote_om.call_get_managed_objects_sync()

    for o, props in objects.items():
        if DEVICE_IFACE in props.keys():
            device = props[DEVICE_IFACE]
            if device["Address"].lower() == uuid.lower():
                return o, props[DEVICE_IFACE]

    return None, None


def set_trusted(path):
    bus = DBusManager().get_bus()
    props = bus.get_proxy_object(
        "org.bluez", path, bus.introspect_sync("org.bluez", path)
    ).get_interface("org.freedesktop.DBus.Properties")
    props.call_set_sync("org.bluez.Device1", "Trusted", True)


def device_is_connected(bus, device):
    device_obj = bus.get_proxy_object(
        BLUEZ_SERVICE_NAME, device, bus.introspect_sync(BLUEZ_SERVICE_NAME, device)
    )
    device_properties = device_obj.get_interface("org.freedesktop.DBus.Properties")
    connected_state = device_properties.call_get_sync(DEVICE_IFACE, "Connected")
    return connected_state


def dev_connect(path):
    bus = DBusManager().get_bus()
    dev = bus.get_proxy_object(
        "org.bluez", path, bus.introspect_sync("org.bluez", path)
    ).get_interface("org.bluez.Device1")
    dev.call_connect_sync()


class Rejected(DBusError):
    # class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class AgentSingleton:
    __instance = None

    @staticmethod
    def get_instance():
        """Static access method."""
        if AgentSingleton.__instance is None:
            AgentSingleton()
        return AgentSingleton.__instance

    @staticmethod
    def clear_instance():
        AgentSingleton.__instance = None

    def __init__(self):
        """Virtually private constructor."""
        self.passkeys = {}
        if AgentSingleton.__instance is None:
            AgentSingleton.__instance = self

            syslog("Registering agent for auto-pairing...")
            try:
                # get the system bus
                bus = DBusManager.get_bus()
                agent = AuthenticationAgent(AGENT_IFACE)
                bus.export(AGENT_PATH, agent)

                obj = bus.get_proxy_object(
                    BLUEZ_SERVICE_NAME,
                    "/org/bluez",
                    bus.introspect_sync(BLUEZ_SERVICE_NAME, "/org/bluez"),
                )

                agent_manager = obj.get_interface("org.bluez.AgentManager1")
                agent_manager.call_register_agent_sync(AGENT_PATH, "NoInputNoOutput")
            except Exception as e:
                syslog(LOG_ERR, str(e))


class AuthenticationAgent(ServiceInterface):
    exit_on_release = True

    def __init__(self, name):
        super().__init__(name)

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @method()
    def Release(self):
        syslog("AuthenticationAgent Release")

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        syslog("AuthenticationAgent AuthorizeService (%s, %s)" % (device, uuid))
        return

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        syslog("AuthenticationAgent RequestPinCode (%s)" % (device))
        set_trusted(device)
        return "000000"

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        syslog("AuthenticationAgent RequestPasskey (%s)" % (device))
        set_trusted(device)
        # passkey = ask("Enter passkey: ")
        # TODO: Implement with RESTful set
        passkey = 0
        agent_instance = AgentSingleton.get_instance()
        if agent_instance:
            if device in agent_instance.passkeys:
                passkey = agent_instance.passkeys[device]
        return int(passkey)

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        syslog(
            "AuthenticationAgent DisplayPasskey (%s, %06u entered %u)"
            % (device, passkey, entered)
        )

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        syslog("AuthenticationAgent DisplayPinCode (%s, %s)" % (device, pincode))

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        syslog("AuthenticationAgent RequestConfirmation (%s, %06d)" % (device, passkey))
        # TODO:  Check if provided passkey matches customer-preset passkey.
        set_trusted(device)
        return

    # Alcon Smart Remote utilizes RequestAuthorization
    # "used for requesting authorization for pairing requests which would otherwise not trigger any action for the user
    # The main situation where this would occur is an incoming SSP pairing request that would trigger the just-works
    # model."
    @method()
    def RequestAuthorization(self, device: "o"):
        syslog("AuthenticationAgent RequestAuthorization (%s)" % (device))
        return

    @method()
    def Cancel(self):
        syslog("AuthenticationAgent Cancel")
