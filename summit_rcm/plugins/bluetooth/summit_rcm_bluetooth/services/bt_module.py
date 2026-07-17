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
PROFILE_UNAVAILABLE_GRACE_SECONDS = 5
PROFILE_UNAVAILABLE_POLL_INTERVAL_SECONDS = 0.1
SERVICE_RESOLUTION_GRACE_SECONDS = 10
SERVICE_RESOLUTION_POLL_INTERVAL_SECONDS = 0.1
# After Numeric Comparison pairing, BlueZ briefly removes/re-adds the device
# D-Bus object while distributing keys. Retry the managed-objects scan so that
# bleConnect doesn't fail during this transitional window.
POST_PAIR_DEVICE_LOOKUP_GRACE_SECONDS = 6
POST_PAIR_DEVICE_LOOKUP_RETRY_INTERVAL_SECONDS = 0.5

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
        requested_uuid = service_uuid.lower()
        for path, interfaces in self.objects.items():
            if path.startswith(device_path):
                service = interfaces.get(BT_SERVICE_IFACE)
                if service and str(variant_to_python(service["UUID"])).lower() == requested_uuid:
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

    async def find_characteristic(self, device_path, char_uuid, service_uuid=""):
        requested_char_uuid = char_uuid.lower()
        requested_service_uuid = service_uuid.lower()
        for path, interfaces in self.objects.items():
            if not path.startswith(device_path):
                continue
            char = interfaces.get(BT_CHARACTERISTIC_IFACE)
            if not char:
                continue
            if str(variant_to_python(char["UUID"])).lower() != requested_char_uuid:
                continue

            if requested_service_uuid:
                service_path = path.rsplit("/", 1)[0]
                service = self.objects.get(service_path, {}).get(BT_SERVICE_IFACE)
                if not service or str(variant_to_python(service["UUID"])).lower() != requested_service_uuid:
                    continue

            return path

        return None

    def available_characteristics(self, device_path, service_uuid=""):
        requested_service_uuid = service_uuid.lower()
        characteristics = []
        for path, interfaces in self.objects.items():
            if not path.startswith(device_path):
                continue

            char = interfaces.get(BT_CHARACTERISTIC_IFACE)
            if not char:
                continue

            service_path = path.rsplit("/", 1)[0]
            service = self.objects.get(service_path, {}).get(BT_SERVICE_IFACE)
            service_uuid_value = ""
            if service:
                service_uuid_value = str(variant_to_python(service["UUID"]))
                if (
                    requested_service_uuid
                    and service_uuid_value.lower() != requested_service_uuid
                ):
                    continue

            characteristics.append(
                f"{variant_to_python(char['UUID'])} ({service_uuid_value or 'unknown service'})"
            )

        return characteristics

    def available_services(self, device_path):
        services = []
        for path, interfaces in self.objects.items():
            if not path.startswith(device_path):
                continue

            service = interfaces.get(BT_SERVICE_IFACE)
            if service:
                services.append(f"{variant_to_python(service['UUID'])} ({path})")

        return services

    async def _connect_device(self, device):
        await device.connect()

        gatt_reload_attempted = False
        deadline = asyncio.get_running_loop().time() + SERVICE_RESOLUTION_GRACE_SECONDS
        while asyncio.get_running_loop().time() < deadline:
            if await device.is_connected() and await device.is_services_resolved():
                # Verify GattService1 D-Bus objects actually exist. After Numeric
                # Comparison pairing, the device may show Connected+ServicesResolved=True
                # from the pairing link but BlueZ has not loaded the GATT profile
                # (br-connection-profile-unavailable). GattService1 objects are absent.
                # Detect this and disconnect+reconnect to establish a proper GATT conn.
                fresh_objects = await self.manager.call_get_managed_objects()
                has_gatt = any(
                    BT_SERVICE_IFACE in ifaces
                    for path, ifaces in fresh_objects.items()
                    if path.startswith(device.get_path())
                )
                if has_gatt:
                    self.logger.info(
                        "Device %s connected with services resolved before GATT cache build",
                        device.get_address(),
                    )
                    await self.mgr_connection_callback(device)
                    return True
                if not gatt_reload_attempted:
                    gatt_reload_attempted = True
                    self.logger.warning(
                        "Device %s: Connected+ServicesResolved but no GattService1 objects; "
                        "disconnecting pairing link to reload GATT profile",
                        device.get_address(),
                    )
                    try:
                        await device.interface.call_disconnect()
                        self.logger.info(
                            "Device %s: GATT-reload disconnect sent", device.get_address()
                        )
                    except Exception as disc_exc:
                        self.logger.warning(
                            "Device %s: GATT-reload disconnect raised: %s",
                            device.get_address(),
                            disc_exc,
                        )
                    await asyncio.sleep(PROFILE_UNAVAILABLE_POLL_INTERVAL_SECONDS)
                    # Re-connect bounded by the time remaining in the grace window
                    # so the reconnect can't overshoot the outer deadline.
                    self.logger.info(
                        "Device %s: GATT-reload: calling Device1.Connect() for bonded reconnect",
                        device.get_address(),
                    )
                    try:
                        await asyncio.wait_for(
                            device.interface.call_connect(),
                            max(0.0, deadline - asyncio.get_running_loop().time()),
                        )
                        self.logger.info(
                            "Device %s: GATT-reload: Device1.Connect() returned (Connected=%s ServicesResolved=%s)",
                            device.get_address(),
                            await device.is_connected(),
                            await device.is_services_resolved(),
                        )
                    except Exception as reload_exc:
                        self.logger.warning(
                            "Device %s: GATT-reload: Device1.Connect() raised %s: %s",
                            device.get_address(),
                            type(reload_exc).__name__,
                            reload_exc,
                        )
            await asyncio.sleep(SERVICE_RESOLUTION_POLL_INTERVAL_SECONDS)

        if await device.is_connected():
            self.logger.info(
                "Device %s connected but services were not resolved before GATT cache build",
                device.get_address(),
            )
            await self.mgr_connection_callback(device)
            return True

        self.logger.error(
            "Device %s failed to reach a connected state", device.get_address()
        )
        return False

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
            success = await self._connect_device(device)
        else:
            # No explicit path supplied (device_interface was None in the REST layer, which
            # happens when find_device() returned None). BlueZ briefly removes and re-adds
            # the device D-Bus object after Numeric Comparison pairing completes (key
            # distribution). Retry the managed-objects scan for up to
            # POST_PAIR_DEVICE_LOOKUP_GRACE_SECONDS before giving up.
            deadline = (
                asyncio.get_running_loop().time() + POST_PAIR_DEVICE_LOOKUP_GRACE_SECONDS
            )
            while not success:
                for path, interfaces in self.objects.items():
                    if path.startswith(self.adapter.path):
                        device = interfaces.get(BT_DEVICE_IFACE)
                        if device and str(variant_to_python(device["Address"])) == address:
                            # Found it; create and connect
                            # NOTE: The 'mgr_connection_callback' will store the device
                            # locally if it connects successfully
                            device = await create_device(
                                address,
                                path,
                                self.characteristic_property_change_callback,
                                self.mgr_connection_callback,
                                self.write_notification_callback,
                                throw_exceptions=self.throw_exceptions,
                            )
                            success = await self._connect_device(device)
                            break

                if success or asyncio.get_running_loop().time() >= deadline:
                    break

                self.logger.info(
                    "Device %s not yet visible in managed objects "
                    "(BlueZ post-pairing transition), retrying in %.1fs "
                    "(%.1fs remaining)...",
                    address,
                    POST_PAIR_DEVICE_LOOKUP_RETRY_INTERVAL_SECONDS,
                    deadline - asyncio.get_running_loop().time(),
                )
                await asyncio.sleep(POST_PAIR_DEVICE_LOOKUP_RETRY_INTERVAL_SECONDS)
                self.objects = await self.manager.call_get_managed_objects()

        if not success:
            self.logger.error("Failed to connect device %s", address)
            if self.throw_exceptions:
                raise RuntimeError(f"Failed to connect device {address}")

        return success

    async def disconnect(self, address, purge):
        """
        Disconnect from the bluetooth device at the designated address
        then purge (if requested) from the adapter's discovered list
        """
        self.logger.info("Disconnecting from %s", address)

        device = self.devices.get(address)
        if device is not None:
            device_path = device.get_path()
            await device.disconnect()
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
                services = []
                for uuid in await device.get_service_uuids():
                    service_path = await self.find_service(device.get_path(), uuid)
                    if service_path:
                        services.append((uuid, service_path))

                for path, interfaces in self.objects.items():
                    if not path.startswith(device.get_path()):
                        continue
                    service_props = interfaces.get(BT_SERVICE_IFACE)
                    if service_props:
                        services.append((variant_to_python(service_props["UUID"]), path))

                for uuid, service_path in services:
                    service = await device.add_service(uuid, service_path)
                    chars_array = await self.find_characteristics(service_path)
                    for char in chars_array:
                        await service.add_characteristic(char["uuid"], char["path"])

                self.logger.debug(
                    "Discovered GATT objects for device %s: services=%s characteristics=%s",
                    address,
                    ", ".join(self.available_services(device.get_path())) or "none",
                    ", ".join(self.available_characteristics(device.get_path())) or "none",
                )
        except Exception as exception:
            self.logger.error(
                "Failed to build services for device %s: %s", address, exception
            )

    async def get_device_service(self, address, service_uuid):
        device = self.devices.get(address)
        if device is None:
            self.logger.error("Device %s was not found", address)
            return None, None

        service = device.get_service(service_uuid)
        if service is None:
            await self.build_device_services(address)
            service = device.get_service(service_uuid)

        return device, service

    async def ensure_device_ready(self, address):
        device = self.devices.get(address)
        if device is None:
            self.logger.error("Device %s was not found", address)
            return None

        connected = await device.is_connected()
        services_resolved = await device.is_services_resolved()
        if connected and services_resolved:
            return device

        self.logger.info(
            "Refreshing GATT connection for device %s before operation "
            "(Connected=%s, ServicesResolved=%s)",
            address,
            connected,
            services_resolved,
        )
        device.disconnect_signal()
        self.devices.pop(address, None)
        await self.connect(address, device.get_path())
        refreshed_device = self.devices.get(address)
        if refreshed_device is not None:
            self.logger.info(
                "Post-refresh GATT state for device %s: Connected=%s ServicesResolved=%s services=%s characteristics=%s",
                address,
                await refreshed_device.is_connected(),
                await refreshed_device.is_services_resolved(),
                ", ".join(self.available_services(refreshed_device.get_path())) or "none",
                ", ".join(self.available_characteristics(refreshed_device.get_path())) or "none",
            )
        else:
            self.logger.error("Post-refresh GATT state for device %s: device not cached", address)

        return refreshed_device

    async def get_device_characteristic(self, address, service_uuid, char_uuid):
        device = await self.ensure_device_ready(address)
        if device is None:
            return None, None, None

        service = device.get_service(service_uuid)
        if service is None:
            await self.build_device_services(address)
            service = device.get_service(service_uuid)

        if service:
            char = service.get_characteristic(char_uuid)
            if char:
                return device, service, char

        deadline = asyncio.get_running_loop().time() + SERVICE_RESOLUTION_GRACE_SECONDS
        char_path = None
        reconnected_during_lookup = False
        while asyncio.get_running_loop().time() < deadline:
            connected = await device.is_connected()
            services_resolved = await device.is_services_resolved()
            if not connected or not services_resolved:
                if reconnected_during_lookup:
                    self.logger.info(
                        "GATT characteristic lookup for device %s still sees Connected=%s ServicesResolved=%s after reconnect",
                        address,
                        connected,
                        services_resolved,
                    )
                else:
                    self.logger.info(
                        "GATT characteristic lookup for device %s saw Connected=%s ServicesResolved=%s; reconnecting before retry",
                        address,
                        connected,
                        services_resolved,
                    )
                    refreshed_device = await self.ensure_device_ready(address)
                    if refreshed_device is None:
                        return None, None, None
                    device = refreshed_device
                    service = device.get_service(service_uuid)
                    if service is None:
                        await self.build_device_services(address)
                        service = device.get_service(service_uuid)
                    if service:
                        char = service.get_characteristic(char_uuid)
                        if char:
                            return device, service, char
                    reconnected_during_lookup = True

            self.objects = await self.manager.call_get_managed_objects()
            char_path = await self.find_characteristic(
                device.get_path(), char_uuid, service_uuid
            )
            if char_path:
                break
            await asyncio.sleep(SERVICE_RESOLUTION_POLL_INTERVAL_SECONDS)

        if not char_path:
            service_characteristics = self.available_characteristics(
                device.get_path(), service_uuid
            )
            all_characteristics = self.available_characteristics(device.get_path())
            services = self.available_services(device.get_path())
            global_services = self.available_services("")
            global_characteristics = self.available_characteristics("")
            device_uuids = await device.get_service_uuids()
            device_connected = await device.is_connected()
            device_services_resolved = await device.is_services_resolved()
            self.logger.error(
                "Characteristic UUID %s not found for service %s and device %s "
                "at path %s; connected=%s services_resolved=%s device UUIDs: %s; "
                "device services: %s; service characteristics: %s; "
                "device characteristics: %s; global services: %s; "
                "global characteristics: %s",
                char_uuid,
                service_uuid,
                address,
                device.get_path(),
                device_connected,
                device_services_resolved,
                ", ".join(device_uuids) if device_uuids else "none",
                ", ".join(services) if services else "none",
                ", ".join(service_characteristics) if service_characteristics else "none",
                ", ".join(all_characteristics) if all_characteristics else "none",
                ", ".join(global_services) if global_services else "none",
                ", ".join(global_characteristics) if global_characteristics else "none",
            )
            return device, service, None

        service_path = char_path.rsplit("/", 1)[0]
        service_props = self.objects.get(service_path, {}).get(BT_SERVICE_IFACE)
        if service is None and service_props:
            service = await device.add_service(
                variant_to_python(service_props["UUID"]), service_path
            )

        char_props = self.objects.get(char_path, {}).get(BT_CHARACTERISTIC_IFACE)
        characteristic_uuid = (
            variant_to_python(char_props["UUID"]) if char_props else char_uuid
        )
        if service:
            char = await service.add_characteristic(characteristic_uuid, char_path)
        else:
            char = await create_characteristic(
                characteristic_uuid,
                char_path,
                device.write_characteristic_notification_callback,
                device.characteristic_property_change_callback,
            )

        return device, service, char

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
            device, _, char = await self.get_device_characteristic(
                address, service_uuid, char_uuid
            )
            if device is not None:
                if char:
                    value = await char.read_value(offset)
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
            device, _, char = await self.get_device_characteristic(
                address, service_uuid, char_uuid
            )
            if device is not None:
                if char:
                    value_bytes = bytearray(value)
                    return await char.write_value(value_bytes, offset)
        except Exception as exception:
            self.logger.error(
                "Failed to write device %s characteristic %s: %s",
                address,
                char_uuid,
                exception,
            )

        return False

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
            device, _, char = await self.get_device_characteristic(
                address, service_uuid, char_uuid
            )
            if device is not None:
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

            self.logger.info(
                "Device %s calling Device1.Connect() (Connected=%s)",
                self.address,
                await self.is_connected(),
            )
            await asyncio.wait_for(
                self.interface.call_connect(), CONNECT_TIMEOUT_SECONDS
            )
        except Exception as exception:
            self.logger.warning(
                "Device %s Device1.Connect() raised %s: %s",
                self.address,
                type(exception).__name__,
                exception,
            )
            if "br-connection-profile-unavailable" in str(exception):
                # The LE pairing link is connected but BlueZ has not loaded the GATT
                # profile for it. Explicitly disconnect to tear down the pairing link,
                # then retry Device1.Connect() which will establish a proper bonded GATT
                # connection and create GattService1 D-Bus objects.
                self.logger.warning(
                    "Device %s: br-connection-profile-unavailable — "
                    "disconnecting to reload GATT profile before retry",
                    self.address,
                )
                try:
                    await self.interface.call_disconnect()
                    self.logger.info(
                        "Device %s: explicit disconnect sent", self.address
                    )
                except Exception as disc_exc:
                    self.logger.warning(
                        "Device %s: explicit disconnect raised: %s",
                        self.address,
                        disc_exc,
                    )
                # Wait for the disconnect to be confirmed by BlueZ
                deadline = (
                    asyncio.get_running_loop().time()
                    + PROFILE_UNAVAILABLE_GRACE_SECONDS
                )
                while asyncio.get_running_loop().time() < deadline:
                    if not await self.is_connected():
                        break
                    await asyncio.sleep(PROFILE_UNAVAILABLE_POLL_INTERVAL_SECONDS)
                self.logger.info(
                    "Device %s: retrying Device1.Connect() after disconnect "
                    "(Connected=%s)",
                    self.address,
                    await self.is_connected(),
                )
                # Retry — this time the device is disconnected so BlueZ will
                # reconnect using bonded credentials and create GATT objects.
                try:
                    await asyncio.wait_for(
                        self.interface.call_connect(), CONNECT_TIMEOUT_SECONDS
                    )
                    self.logger.info(
                        "Device %s: Device1.Connect() retry succeeded "
                        "(Connected=%s ServicesResolved=%s)",
                        self.address,
                        await self.is_connected(),
                        await self.is_services_resolved(),
                    )
                except Exception as retry_exc:
                    self.logger.warning(
                        "Device %s: Device1.Connect() retry raised: %s (%s)",
                        self.address,
                        retry_exc,
                        type(retry_exc).__name__,
                    )
                    if self.throw_exceptions:
                        raise
                return

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
        service = self.get_service(uuid)
        if service:
            return service

        service = await create_service(
            uuid,
            path,
            self.write_characteristic_notification_callback,
            self.characteristic_property_change_callback,
        )
        self.services.append(service)
        return service

    def get_service(self, uuid):
        """
        Returns the device service matching the UUID
        None if the service is not found
        """
        requested_uuid = uuid.lower()
        for service in self.services:
            if service.get_uuid().lower() == requested_uuid:
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
        interesting_properties = {
            key: variant_to_python(value)
            for key, value in changed_properties.items()
            if key in {
                "Connected",
                "ServicesResolved",
                "Paired",
                "Bonded",
                "Trusted",
                "DisconnectReason",
            }
        }
        if interesting_properties or invalidated_properties:
            self.logger.info(
                "Device %s property change: changed=%s invalidated=%s",
                self.address,
                interesting_properties,
                invalidated_properties,
            )

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
        characteristic = self.get_characteristic(uuid)
        if characteristic:
            return characteristic

        char = await create_characteristic(
            uuid,
            path,
            self.write_characteristic_notification_callback,
            self.characteristic_property_change_callback,
        )
        self.characteristics.append(char)
        return char

    def get_characteristic(self, uuid):
        """
        Returns the service characteristic matching the UUID
        None if the characteristic is not found
        """
        requested_uuid = uuid.lower()
        for char in self.characteristics:
            if char.get_uuid().lower() == requested_uuid:
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
        return variant_to_python(await self.interface.get_notifying())

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
            return False
        await self.write_characteristic_success_callback()
        return True

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


async def bt_connect(bt, address, device_path=""):
    """
    Connect to the bluetooth device at the designated address
    """
    if bt:
        return await bt.connect(address, device_path)
    return False


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
    Value is returned as a bytearray, or None on failure
    """
    if bt:
        return await bt.read_characteristic(address, service_uuid, char_uuid)
    return None


async def bt_write_characteristic(bt, address, service_uuid, char_uuid, value):
    """
    Write a value to the given characteristic for the given device/service
    The value is an array of bytes
    """
    if bt:
        return await bt.write_characteristic(address, service_uuid, char_uuid, value)
    return False


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
