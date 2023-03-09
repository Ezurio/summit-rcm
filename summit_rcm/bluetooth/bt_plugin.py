from typing import Optional, Tuple, List


class BluetoothPlugin(object):
    @property
    def device_commands(self) -> List[str]:
        return []

    @property
    def adapter_commands(self) -> List[str]:
        return []

    def ProcessDeviceCommand(
        self,
        bus,
        command,
        device_uuid: str,
        device: str,
        adapter_obj: str,
        post_data,
        remove_device_method=None,
    ) -> Tuple[bool, str]:
        """Process a device-specific command."""
        return False, ""

    def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_obj: str,
        post_data,
    ) -> Tuple[bool, str, Optional[dict]]:
        """Process an adapter-specific command."""
        return False, "", None

    def DeviceRemovedNotify(self, device_uuid: str, device: str):
        """Notify plugin that device was removed/unpaired."""
        return

    def ControllerResetNotify(self, controller_name: str, adapter_obj: str):
        """Notify plugin that BT controller was reset, all state reset."""
        self.ControllerRemovedNotify(controller_name, adapter_obj)
        self.ControllerAddedNotify(controller_name, adapter_obj)

    def ControllerRemovedNotify(self, controller_name: str, adapter_obj: str):
        """Notify plugin that BT controller was removed, all state reset."""
        return

    def ControllerAddedNotify(self, controller_name: str, adapter_obj: str):
        """Notify plugin that (probably previously removed) BT controller was added, all state
        reset."""
        return

    def DeviceAddedNotify(self, device: str, device_uuid: str, device_obj: str):
        """Notify plugin that (probably previously removed) BT device was added
        :param device: string specifying dbus object path
        """
        return
