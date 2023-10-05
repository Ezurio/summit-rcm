"""
Module for defining a common base class for Bluetooth plugins
"""

from typing import Optional, Tuple, List
from dbus_fast.aio.proxy_object import ProxyInterface, ProxyObject


class BluetoothPlugin(object):
    @property
    def device_commands(self) -> List[str]:
        return []

    @property
    def adapter_commands(self) -> List[str]:
        return []

    async def ProcessDeviceCommand(
        self,
        bus,
        command,
        device_uuid: str,
        device_interface: Optional[ProxyInterface],
        adapter_interface: Optional[ProxyInterface],
        post_data,
        remove_device_method=None,
    ) -> Tuple[bool, str]:
        """Process a device-specific command."""
        return False, ""

    async def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_interface: Optional[ProxyInterface],
        post_data,
    ) -> Tuple[bool, str, Optional[dict]]:
        """Process an adapter-specific command."""
        return False, "", None

    async def DeviceRemovedNotify(
        self, device_uuid: str, device_interface: ProxyInterface
    ):
        """Notify plugin that device was removed/unpaired."""
        return

    async def ControllerResetNotify(
        self, controller_name: str, adapter_obj: ProxyObject
    ):
        """Notify plugin that BT controller was reset, all state reset."""
        await self.ControllerRemovedNotify(controller_name, adapter_obj)
        await self.ControllerAddedNotify(controller_name, adapter_obj)

    async def ControllerRemovedNotify(
        self, controller_name: str, adapter_obj: ProxyObject
    ):
        """Notify plugin that BT controller was removed, all state reset."""
        return

    async def ControllerAddedNotify(
        self, controller_name: str, adapter_obj: ProxyObject
    ):
        """Notify plugin that (probably previously removed) BT controller was added, all state
        reset."""
        return

    async def DeviceAddedNotify(
        self, device: str, device_uuid: str, device_obj: ProxyObject
    ):
        """Notify plugin that (probably previously removed) BT device was added
        :param device: string specifying dbus object path
        """
        return
