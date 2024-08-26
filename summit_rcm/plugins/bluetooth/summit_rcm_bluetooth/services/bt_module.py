#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
bt_module.py

Bluetooth API for Sentrius IG devices
"""

import threading
import logging
import asyncio
from typing import Dict
from dbus_fast import DBusError, Variant
from dbus_fast.aio.proxy_object import ProxyInterface, ProxyObject
from summit_rcm.dbus_manager import DBusManager
from summit_rcm.utils import variant_to_python

BT_OBJ = "org.bluez"
BT_OBJ_PATH = "/org/bluez/hci0"
BT_ADAPTER_IFACE = "org.bluez.Adapter1"
BT_DEVICE_IFACE = "org.bluez.Device1"
BT_SERVICE_IFACE = "org.bluez.GattService1"
BT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"
DBUS_OBJ_MGR_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
CONNECT_TIMEOUT_SECONDS = 60

RESULT_SUCCESS = 0
RESULT_ERR = -1


class BtMgr(threading.Thread):
    """
    Class that manages all bluetooth API functionality
    """

    def __init__(
        self,
        characteristic_property_change_callback,
        connection_callback=None,
        write_notification_callback=None,
        throw_exceptions=False,
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initalizing BtMgr")
        self.throw_exceptions = throw_exceptions

        self.devices: Dict[str, Device] = {}
        self.objects = {}
        self.manager: ProxyInterface = None
        self.adapter: ProxyInterface = None

        # Save custom callbacks with the client
        self.characteristic_property_change_callback = (
            characteristic_property_change_callback
        )
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback

        # Call base constructor
        super().__init__()

    async def start_discovery(self):
        """
        Activate bluetooth discovery of peripherals
        """
        self.logger.info("Starting Discovery")
        await self.adapter.call_start_discovery()

    async def stop_discovery(self):
        """
        Deactivate bluetooth discovery of peripherals
        """
        self.logger.info("Stopping Discovery")
        await self.adapter.call_stop_discovery()

    async def find_service(self, device_path, service_uuid):
        """
        Returns a path to the service for the given device identified by the UUID
        """
        for path, interfaces in self.objects.items():
            if path.startswith(device_path):
                service = interfaces.get(BT_SERVICE_IFACE)
                if service and str(variant_to_python(service["UUID"])) == service_uuid:
                    return path
        return None

    async def find_characteristics(self, service_path):
        """
        Returns an array of dictionaries containing the UUID and path for
        every characteristic associated with the given service
        """
        chars_array = []
        for path, interfaces in self.objects.items():
            if path.startswith(service_path):
                char = interfaces.get(BT_CHARACTERISTIC_IFACE)
                if char:
                    char_elements = {}
                    char_elements["uuid"] = variant_to_python(char["UUID"])
                    char_elements["path"] = path
                    chars_array.append(char_elements)

        return chars_array

    async def connect(self, address, device_path=""):
        """
        Connect to the bluetooth device at the designated address
        """
        self.logger.info("Connecting to %s", address)
        self.objects = await self.manager.call_get_managed_objects()

        success = False
        if device_path:
            # NOTE: The 'mgr_connection_callback' will store the device locally if it connects
            # successfully
            device = await create_device(
                address,
                device_path,
                self.characteristic_property_change_callback,
                self.mgr_connection_callback,
                self.write_notification_callback,
                throw_exceptions=self.throw_exceptions,
            )
            await device.connect()
            success = True
        else:
            for path, interfaces in self.objects.items():
                if path.startswith(self.adapter.path):
                    device = interfaces.get(BT_DEVICE_IFACE)
                    if device and str(variant_to_python(device["Address"])) == address:
                        # Found it; create and connect
                        # NOTE: The 'mgr_connection_callback' will store the device locally if it
                        # connects successfully
                        device = await create_device(
                            address,
                            path,
                            self.characteristic_property_change_callback,
                            self.mgr_connection_callback,
                            self.write_notification_callback,
                            throw_exceptions=self.throw_exceptions,
                        )
                        await device.connect()
                        success = True

        if not success:
            self.logger.error("Device %s was not found", address)

    async def disconnect(self, address, purge):
        """
        Disconnect from the bluetooth device at the designated address
        then purge (if requested) from the adapter's discovered list
        """
        self.logger.info("Disconnecting from %s", address)

        device = self.devices.get(address)
        if device is not None:
            device_path = device.get_path()
            device.disconnect()
            if purge:
                await self.adapter.call_remove_device(device_path)
        else:
            self.logger.error("Device %s was not found", address)

    async def build_device_services(self, address):
        """
        Build a list of services for the given device
        """
        self.logger.info("Building services and characteristics for %s", address)

        try:
            self.objects = await self.manager.call_get_managed_objects()

            device = self.devices.get(address)
            if device is not None:
                uuids = await device.get_service_uuids()
                for uuid in uuids:
                    service_path = await self.find_service(device.get_path(), uuid)
                    if service_path:
                        await device.add_service(uuid, service_path)
                        service = device.get_service(uuid)

                        chars_array = await self.find_characteristics(service_path)
                        for char in chars_array:
                            await service.add_characteristic(char["uuid"], char["path"])
        except Exception as exception:
            self.logger.error(
                "Failed to build services for device %s: %s", address, exception
            )

    async def get_device_services(self, address):
        """
        Returns all the services and characteristics for the given device
        """
        self.logger.info("Retrieving services and characteristics for %s", address)

        services = {}
        device = self.devices.get(address)
        if device is not None:
            services["services"] = await device.get_services()
        else:
            self.logger.error("Device %s was not found", address)

        return services

    async def read_characteristic(self, address, service_uuid, char_uuid, offset=0):
        """
        Returns the characteristic value for the given device/service
        None if reading the characteristic was a failure
        """
        value = None
        self.logger.info(
            "Reading characteristic %s in service %s for device %s",
            char_uuid,
            service_uuid,
            address,
        )

        try:
            device = self.devices.get(address)
            if device is not None:
                service = device.get_service(service_uuid)
                if service:
                    char = service.get_characteristic(char_uuid)
                    if char:
                        value = await char.read_value(offset)
                    else:
                        self.logger.error(
                            "Characteristic UUID %s not found for service %s and device %s",
                            char_uuid,
                            service_uuid,
                            address,
                        )
                else:
                    self.logger.error(
                        "Service UUID %s not found for device %s", service_uuid, address
                    )
            else:
                self.logger.error("Device %s was not found", address)
        except Exception as exception:
            self.logger.error(
                "Failed to read device %s characteristic %s: %s",
                address,
                char_uuid,
                exception,
            )

        return value

    async def write_characteristic(
        self, address, service_uuid, char_uuid, value, offset=0
    ):
        """
        Write a value to the given characteristic for the given device/service
        The value is an array of bytes
        """
        self.logger.info(
            "Writing to characteristic %s in service %s for device %s",
            char_uuid,
            service_uuid,
            address,
        )

        try:
            device = self.devices.get(address)
            if device is not None:
                service = device.get_service(service_uuid)
                if service:
                    char = service.get_characteristic(char_uuid)
                    if char:
                        # Convert the value to a DBus-formatted byte array
                        value_bytes = bytearray(value)

                        # Write the value
                        await char.write_value(value_bytes, offset)
                    else:
                        self.logger.error(
                            "Characteristic UUID %s not found for service %s and device %s",
                            char_uuid,
                            service_uuid,
                            address,
                        )
                else:
                    self.logger.error(
                        "Service UUID %s not found for device %s", service_uuid, address
                    )
            else:
                self.logger.error("Device %s was not found", address)
        except Exception as exception:
            self.logger.error(
                "Failed to write device %s characteristic %s: %s",
                address,
                char_uuid,
                exception,
            )

    async def configure_characteristic_notification(
        self, address, service_uuid, char_uuid, enable
    ):
        """
        Enable/Disable notifications for the given device characteristic
        """
        if enable:
            self.logger.info(
                "Starting notifications for characteristic %s in service %s for device %s",
                char_uuid,
                service_uuid,
                address,
            )
        else:
            self.logger.info(
                "Stopping notifications for characteristic %s in service %s for device %s",
                char_uuid,
                service_uuid,
                address,
            )

        try:
            device: Device = self.devices.get(address)
            if device is not None:
                service: Service = device.get_service(service_uuid)
                if service:
                    char: Characteristic = service.get_characteristic(char_uuid)
                    if char:
                        if enable:
                            if not await char.is_notifying():
                                await char.start_notifications()
                            else:
                                self.logger.error(
                                    "Characteristic %s is already sending notifications",
                                    char_uuid,
                                )
                        else:
                            await char.stop_notifications()
                    else:
                        self.logger.error(
                            "Characteristic UUID %s not found for service %s and device %s",
                            char_uuid,
                            service_uuid,
                            address,
                        )
                else:
                    self.logger.error(
                        "Service UUID %s not found for device %s", service_uuid, address
                    )
            else:
                self.logger.error("Device %s was not found", address)
        except Exception as exception:
            self.logger.error(
                "Failed to configure characteristic notifications for device %s "
                "characteristic %s: %s",
                address,
                char_uuid,
                exception,
            )

    async def mgr_connection_callback(self, device):
        data = {}
        data["connected"] = await device.is_connected()
        data["address"] = device.get_address()
        if data["connected"]:
            # Add the new connected device to the managed device array
            self.devices[data["address"]] = device
            self.logger.info(
                "Added device %s, path %s, list count %d",
                data["address"],
                device.get_path(),
                len(self.devices),
            )

            # Build the list of services for the newly connected device
            await self.build_device_services(data["address"])
        elif not data["connected"]:
            # Disconnected; cleanup the device
            device.disconnect_signal()
            device2 = self.devices.pop(data["address"], None)
            if device2 is None:
                self.logger.info(
                    "No device to remove for %s, list count %d",
                    data["address"],
                    len(self.devices),
                )
            else:
                self.logger.info(
                    "Removed device %s, list count %d",
                    data["address"],
                    len(self.devices),
                )

        # Forward the connection data to the client (if callback provided)
        if self.connection_callback is not None:
            await self.connection_callback(data)


async def create_bt_mgr(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
    throw_exceptions=False,
) -> BtMgr:
    """
    Async wrapper to create a BtMgr object
    """

    bt_mgr = BtMgr(
        characteristic_property_change_callback,
        connection_callback,
        write_notification_callback,
        throw_exceptions,
    )

    # Get DBus objects
    bus = await DBusManager().get_bus()
    bt_mgr.manager = bus.get_proxy_object(
        BT_OBJ, "/", await bus.introspect(BT_OBJ, "/")
    ).get_interface(DBUS_OBJ_MGR_IFACE)
    bt_mgr.adapter = bus.get_proxy_object(
        BT_OBJ, BT_OBJ_PATH, await bus.introspect(BT_OBJ, BT_OBJ_PATH)
    ).get_interface(BT_ADAPTER_IFACE)
    bt_mgr.objects = await bt_mgr.manager.call_get_managed_objects()

    # Register signal handlers
    bt_mgr.manager.on_interfaces_added(discovery_callback)

    # Power on the bluetooth module
    await bt_mgr.adapter.set_powered(True)

    bt_mgr.start()

    return bt_mgr


class Device:
    """
    Class that encapsulates a bluetooth device
    """

    def __init__(
        self,
        address,
        path,
        property_change_callback,
        connection_callback,
        write_notification_callback=None,
        throw_exceptions=False,
    ):
        self.logger = logging.getLogger(__name__)
        self.address = address
        self.property_change_callback = property_change_callback
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback
        self.services: list[Service] = []

        self.path = path
        self.properties_signal = None
        self.throw_exceptions = throw_exceptions

        self.object: ProxyObject = None
        self.interface: ProxyInterface = None
        self.properties: ProxyInterface = None

    async def connect(self):
        """
        Connect to the device
        """
        try:
            # Connect to the device property signals to receive notifications
            if self.properties_signal is None:
                self.properties.on_properties_changed(self.properties_changed)
                self.properties_signal = self.properties_changed

            await asyncio.wait_for(
                self.interface.call_connect(), CONNECT_TIMEOUT_SECONDS
            )
        except Exception as exception:
            self.logger.error(
                "Failed to connect device %s: %s", self.address, exception
            )
            if self.throw_exceptions:
                raise

    async def disconnect(self):
        """
        Disconnect from a device
        """
        try:
            await self.interface.call_disconnect()
        except Exception as exception:
            self.logger.error(
                "Failed to disconnect device %s: %s", self.address, exception
            )
            if self.throw_exceptions:
                raise

    async def add_service(self, uuid, path):
        """
        Create and store a new service linked to this device
        """
        service = await create_service(
            uuid,
            path,
            self.write_characteristic_notification_callback,
            self.characteristic_property_change_callback,
        )
        self.services.append(service)

    def get_service(self, uuid):
        """
        Returns the device service matching the UUID
        None if the service is not found
        """
        for service in self.services:
            if service.get_uuid() == uuid:
                return service

        return None

    async def get_services(self):
        """
        Returns a dictionary of dictionaries including each device's service
        characteristic properties identified by the service UUID
        """
        services_dict = {}
        for service in self.services:
            service_chars = {}
            service_chars["characteristics"] = await service.get_characteristics()
            services_dict[service.get_uuid()] = service_chars

        return services_dict

    def get_path(self):
        """
        Returns the device path
        """
        return self.path

    def get_address(self):
        """
        Returns the device address
        """
        return self.address

    async def get_service_uuids(self):
        """
        Returns all of the UUIDs of the device services
        """
        uuids = []
        try:
            # Due to dbus-fast's snake case conversion, the "UUIDs" property getter is translated
            # as "get_uui_ds()"
            uuids = variant_to_python(await self.interface.get_uui_ds())
        except BaseException:
            # Ignore; means we are not connected
            pass

        return uuids

    async def is_connected(self):
        """
        Returns True if currently connected to the device; false otherwise
        """
        connected = False
        try:
            connected = variant_to_python(await self.interface.get_connected())
        except BaseException:
            # Ignore; means we are not connected
            pass

        return connected

    async def is_services_resolved(self):
        """
        Returns True if all the device services have been discovered; false otherwise
        """
        resolved = False
        try:
            resolved = variant_to_python(await self.interface.get_services_resolved())
        except BaseException:
            # Ignore; means we are not connected
            pass

        return resolved

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties.off_properties_changed(self.properties_signal)
            self.properties_signal = None

        for service in self.services:
            service.disconnect_signal()

    async def properties_changed(
        self, interface, changed_properties, invalidated_properties
    ):
        """
        A callback when a device property changes

        Notifies the client when the device has been both connected
        and all services have been discovered
        """
        if "Connected" in changed_properties and not variant_to_python(
            changed_properties["Connected"]
        ):
            # Send notification that device disconnected
            await self.connection_callback(self)
        if (
            "ServicesResolved" in changed_properties
            and variant_to_python(changed_properties["ServicesResolved"])
            and await self.is_connected()
        ):
            # Send notification that the device is connected and services discovered
            await self.connection_callback(self)

    async def write_characteristic_notification_callback(self, data):
        """
        Callback for a managed characteristic write operation
        Includes data on the success/failure of the write
        Package the device address and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data["address"] = self.address
            await self.write_notification_callback(data)

    async def characteristic_property_change_callback(self, data):
        """
        Callback for a managed characteristic property change
        Includes the characteristic value that changed
        Package the device address and forward the notification to the client
        """
        data["address"] = self.address
        await self.property_change_callback(data)


async def create_device(
    address,
    path,
    property_change_callback,
    connection_callback,
    write_notification_callback=None,
    throw_exceptions=False,
) -> Device:
    """
    Async wrapper to create a Device object
    """

    device = Device(
        address,
        path,
        property_change_callback,
        connection_callback,
        write_notification_callback,
        throw_exceptions,
    )

    bus = await DBusManager().get_bus()
    device.object = bus.get_proxy_object(
        BT_OBJ, path, await bus.introspect(BT_OBJ, path)
    )
    device.interface = device.object.get_interface(BT_DEVICE_IFACE)
    device.properties = device.object.get_interface(DBUS_PROP_IFACE)

    return device


class Service:
    """
    Class that encapsulates a bluetooth device service
    """

    def __init__(
        self, uuid, path, property_change_callback, write_notification_callback=None
    ):
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid
        self.path = path
        self.property_change_callback = property_change_callback
        self.write_notification_callback = write_notification_callback
        self.characteristics = []

        self.object: ProxyObject = None
        self.interface: ProxyInterface = None
        self.properties: ProxyInterface = None
        self.properties_signal = None

    async def add_characteristic(self, uuid, path):
        char = await create_characteristic(
            uuid,
            path,
            self.write_characteristic_notification_callback,
            self.characteristic_property_change_callback,
        )
        self.characteristics.append(char)

    def get_characteristic(self, uuid):
        """
        Returns the service characteristic matching the UUID
        None if the characteristic is not found
        """
        for char in self.characteristics:
            if char.get_uuid() == uuid:
                return char

        return None

    async def get_characteristics(self):
        """
        Returns an array of dictionaries including each service's characteristic
        properties (UUID and flags)
        """
        char_array = []
        for char in self.characteristics:
            char_props = {}
            char_flags = {}

            char_flags["Flags"] = await char.get_flags()
            char_props[char.get_uuid()] = char_flags
            char_array.append(char_props)

        return char_array

    def get_uuid(self):
        """
        Returns the UUID for the service
        """
        return self.uuid

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties.off_properties_changed(self.properties_signal)
            self.properties_signal = None

        for char in self.characteristics:
            char.disconnect_signal()

    async def write_characteristic_notification_callback(self, data):
        """
        Callback for a managed characteristic write operation
        Includes data on the success/failure of the write
        Package the service UUID and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data["service_uuid"] = self.uuid
            await self.write_notification_callback(data)

    async def characteristic_property_change_callback(self, data):
        """
        Callback for a managed characteristic property change
        Includes the characteristic value that changed
        Package the service UUID and forward the notification to the client
        """
        data["service_uuid"] = self.uuid
        await self.property_change_callback(data)


async def create_service(
    uuid, path, property_change_callback, write_notification_callback=None
) -> Service:
    """
    Async wrapper to create a Service object
    """

    service = Service(uuid, path, property_change_callback, write_notification_callback)

    bus = await DBusManager().get_bus()
    service.object = bus.get_proxy_object(
        BT_OBJ, path, await bus.introspect(BT_OBJ, path)
    )
    service.interface = service.object.get_interface(BT_SERVICE_IFACE)
    service.properties = service.object.get_interface(DBUS_PROP_IFACE)

    return service


class Characteristic:
    """
    Class that encapsulates a bluetooth device characteristic
    """

    def __init__(
        self, uuid, path, property_change_callback, write_notification_callback=None
    ):
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid
        self.path = path
        self.property_change_callback = property_change_callback
        self.write_notification_callback = write_notification_callback

        self.object: ProxyObject = None
        self.interface: ProxyInterface = None
        self.properties: ProxyInterface = None
        self.properties_signal = self.characteristic_property_change_callback

    def get_uuid(self):
        """
        Returns the UUID for the characteristic
        """
        return self.uuid

    async def get_flags(self):
        """
        Returns all of the characteristic flags
        """
        return variant_to_python(await self.interface.get_flags())

    async def is_notifying(self):
        """
        Returns whether or not the characteristic is notifying on its value changes
        """
        return variant_to_python(self.interface.get_notifying())

    async def read_value(self, offset):
        """
        Returns the value associated with this characteristic
        The value is an array of bytes
        """
        return await self.interface.call_read_value(
            {"offset": Variant("q", int(offset))}
        )

    async def write_value(self, value, offset):
        """
        Write a value to this characteristic
        The value is an array of bytes
        """
        try:
            await self.interface.call_write_value(
                bytearray(value), {"offset": Variant("q", int(offset))}
            )
        except DBusError as exception:
            await self.write_characteristic_error_callback(exception)
            return
        await self.write_characteristic_success_callback()

    async def start_notifications(self):
        """
        Start sending notifications on this characteristic's property changes
        """
        await self.interface.call_start_notify()

    async def stop_notifications(self):
        """
        Stop sending notifications on this characteristic's property changes
        """
        await self.interface.call_stop_notify()

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties.off_properties_changed(self.properties_signal)
            self.properties_signal = None

    async def write_characteristic_success_callback(self):
        """
        Callback for a successful write operation
        Package the characteristic UUID and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data = {}
            data["result"] = RESULT_SUCCESS
            data["char_uuid"] = self.uuid
            await self.write_notification_callback(data)

    async def write_characteristic_error_callback(self, dbus_error: DBusError):
        """
        Callback for a failed write operation
        Package the characteristic UUID and error, then forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data = {}
            data["result"] = RESULT_ERR
            data["char_uuid"] = self.uuid
            data["error"] = str(dbus_error)
            await self.write_notification_callback(data)

    async def characteristic_property_change_callback(
        self, interface, changed_properties, invalidated_properties
    ):
        """
        Callback for all of this characteristic's property changes
        On value changes, package the characteristic's UUID and new value
        and forward the notification to the client
        """
        for property in changed_properties:
            if property == "Value":
                data = {}
                data["char_uuid"] = self.uuid
                data["value"] = changed_properties[property]
                await self.property_change_callback(data)


async def create_characteristic(
    uuid, path, property_change_callback, write_notification_callback=None
) -> Characteristic:
    """
    Async wrapper to create a Characteristic object
    """
    characteristic = Characteristic(
        uuid, path, property_change_callback, write_notification_callback
    )

    bus = await DBusManager().get_bus()
    characteristic.object = bus.get_proxy_object(
        BT_OBJ, path, await bus.introspect(BT_OBJ, path)
    )
    characteristic.interface = characteristic.object.get_interface(
        BT_CHARACTERISTIC_IFACE
    )
    characteristic.properties = characteristic.object.get_interface(DBUS_PROP_IFACE)
    characteristic.properties.on_properties_changed(
        characteristic.characteristic_property_change_callback
    )

    return characteristic


async def bt_init(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
):
    """
    Initialize the IG bluetooth API
    Returns the device manager instance, to be used in bt_* calls
    """
    try:
        bt = await create_bt_mgr(
            discovery_callback,
            characteristic_property_change_callback,
            connection_callback,
            write_notification_callback,
        )
        return bt
    except Exception as exception:
        logging.getLogger(__name__).error("Cannot open BT interface: %s", exception)
        return None


async def bt_start_discovery(bt):
    """Activate bluetooth discovery of peripherals"""
    if bt:
        await bt.start_discovery()


async def bt_stop_discovery(bt):
    """Deactivate bluetooth discovery of peripherals"""
    if bt:
        await bt.stop_discovery()


async def bt_connect(bt, address):
    """
    Connect to the bluetooth device at the designated address
    """
    if bt:
        await bt.connect(address)


async def bt_disconnect(bt, address, purge):
    """
    Disconnect from the bluetooth device at the designated address
    """
    if bt:
        await bt.disconnect(address, purge)


async def bt_device_services(bt, address):
    """
    Returns all the services and characteristics for the given device
    """
    if bt:
        return await bt.get_device_services(address)


async def bt_read_characteristic(bt, address, service_uuid, char_uuid):
    """
    Read a value to the given characteristic for the given device/service
    Value is returned in the 'characteristic_property_change_callback'
    """
    if bt:
        await bt.read_characteristic(address, service_uuid, char_uuid)


async def bt_write_characteristic(bt, address, service_uuid, char_uuid, value):
    """
    Write a value to the given characteristic for the given device/service
    The value is an array of bytes
    """
    if bt:
        await bt.write_characteristic(address, service_uuid, char_uuid, value)


async def bt_config_characteristic_notification(
    bt, address, service_uuid, char_uuid, enable
):
    """
    Enable/Disable notifications for the given device characteristic
    """
    if bt:
        await bt.configure_characteristic_notification(
            address, service_uuid, char_uuid, enable
        )
