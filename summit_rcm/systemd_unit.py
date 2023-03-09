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


class SystemdUnit(object):
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
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not read 'ActiveState' of {self.unit_file}: {str(e)}",
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
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not activate unit {str(self.unit_file)}: {str(e)}",
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
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not deactivate the unit {str(self.unit_file)}: {str(e)}",
            )
            return False
