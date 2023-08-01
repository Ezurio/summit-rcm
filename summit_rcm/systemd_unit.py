"""
Module to support interface with systemd units (services, sockets, etc.)
"""

from syslog import LOG_ERR, syslog
from dbus_fast import Message, MessageType, Variant
from .dbus_manager import DBusManager
from .definition import (
    SYSTEMD_BUS_NAME,
    SYSTEMD_MAIN_OBJ,
    SYSTEMD_MANAGER_IFACE,
    SYSTEMD_UNIT_ACTIVE_STATE_PROP,
    SYSTEMD_UNIT_IFACE,
    DBUS_PROP_IFACE,
)

SYSTEMD_UNIT_VALID_CONFIG_STATES = ["active", "inactive"]


class SystemdUnit(object):
    """
    Base helper class that facilitates interface with systemd units (services, sockets, etc.)
    """

    def __init__(self, unit_file: str) -> None:
        self.unit_file = unit_file

    async def get_active_state(self) -> str:
        """
        The current 'ActiveState' value for the unit as a string. Possible values are:
        - active
        - reloading
        - inactive
        - failed
        - activating
        - deactivating
        - unknown (error state added by us)

        See below for more info:
        https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html
        """
        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=SYSTEMD_BUS_NAME,
                    path=SYSTEMD_MAIN_OBJ,
                    interface=SYSTEMD_MANAGER_IFACE,
                    member="LoadUnit",
                    signature="s",
                    body=[self.unit_file],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            unit_obj_path = reply.body[0]

            reply = await bus.call(
                Message(
                    destination=SYSTEMD_BUS_NAME,
                    path=unit_obj_path,
                    interface=DBUS_PROP_IFACE,
                    member="Get",
                    signature="ss",
                    body=[SYSTEMD_UNIT_IFACE, SYSTEMD_UNIT_ACTIVE_STATE_PROP],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return (
                reply.body[0].value
                if isinstance(reply.body[0], Variant)
                else str(reply.body[0])
            )
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Could not read 'ActiveState' of {self.unit_file}: {str(exception)}",
            )
            return "unknown"

    async def activate(self) -> bool:
        """
        Activate the unit
        """
        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=SYSTEMD_BUS_NAME,
                    path=SYSTEMD_MAIN_OBJ,
                    interface=SYSTEMD_MANAGER_IFACE,
                    member="StartUnit",
                    signature="ss",
                    body=[self.unit_file, "replace"],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return True
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Could not activate unit {str(self.unit_file)}: {str(exception)}",
            )
            return False

    async def deactivate(self) -> bool:
        """
        Deactivate the unit
        """
        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=SYSTEMD_BUS_NAME,
                    path=SYSTEMD_MAIN_OBJ,
                    interface=SYSTEMD_MANAGER_IFACE,
                    member="StopUnit",
                    signature="ss",
                    body=[self.unit_file, "replace"],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return True
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Could not deactivate the unit {str(self.unit_file)}: {str(exception)}",
            )
            return False


class AlreadyActiveError(Exception):
    """
    Custom error class for when a user requests to activate a systemd service, but it's already
    active.
    """


class AlreadyInactiveError(Exception):
    """
    Custom error class for when a user requests to deactivate a systemd service, but it's already
    inactive.
    """


class ActivationFailedError(Exception):
    """
    Custom error class for when a user requests to activate a systemd service, but the activation
    fails.
    """


class DeactivationFailedError(Exception):
    """
    Custom error class for when a user requests to deactivate a systemd service, but the
    deactivation fails.
    """
