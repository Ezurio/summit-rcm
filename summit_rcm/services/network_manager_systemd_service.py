#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Module to support interfacing with NetworkManager via systemd and D-Bus
"""


from collections.abc import Awaitable, Callable
from summit_rcm.dbus_manager import DBusManager
from summit_rcm.definition import DBUS_PROP_IFACE, SYSTEMD_BUS_NAME
from summit_rcm.systemd_unit import SystemdUnit
from summit_rcm.utils import Singleton

NETWORK_MANAGER_SERVICE_FILE = "NetworkManager.service"
NETWORK_MANAGER_SYSTEMD_UNIT_PATH = (
    "/org/freedesktop/systemd1/unit/NetworkManager_2eservice"
)


class NetworkManagerSystemdService(SystemdUnit, metaclass=Singleton):
    """
    Service to handle interfacing with NetworkManager via systemd and D-Bus
    """

    def __init__(self) -> None:
        super().__init__(NETWORK_MANAGER_SERVICE_FILE)
        self.handlers: list[Callable[[str], Awaitable[None]]] = []

    async def properties_changed_handler(
        self,
        _interface_name: str,
        changed_properties: dict,
        _invalidated_properties: dict,
    ):
        """
        Handler for the 'PropertiesChanged' signal for the NetworkManager D-Bus interface
        """
        if "ActiveState" in changed_properties:
            new_state = changed_properties["ActiveState"].value
            for handler in self.handlers:
                await handler(new_state)

    async def subscribe(self, handler: Callable[[str], Awaitable[None]] = None):
        """
        Subscribe to the 'PropertiesChanged' signal for the NetworkManager D-Bus interface
        """
        if handler is None:
            raise ValueError("A valid handler must be provided")

        if handler in self.handlers:
            return

        self.handlers.append(handler)
        bus = await DBusManager().get_bus()
        proxy_object = bus.get_proxy_object(
            SYSTEMD_BUS_NAME,
            NETWORK_MANAGER_SYSTEMD_UNIT_PATH,
            await bus.introspect(
                SYSTEMD_BUS_NAME,
                NETWORK_MANAGER_SYSTEMD_UNIT_PATH,
            ),
        )
        interface = proxy_object.get_interface(DBUS_PROP_IFACE)
        interface.on_properties_changed(self.properties_changed_handler)
