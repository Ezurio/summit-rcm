from syslog import syslog, LOG_ERR
from typing import Optional
from dbus_fast.constants import BusType
from dbus_fast.aio import MessageBus
from summit_rcm.utils import Singleton


class DBusManager(object, metaclass=Singleton):
    def __init__(self) -> None:
        self._bus = None

    async def get_bus(self) -> Optional[MessageBus]:
        if self._bus is None:
            try:
                self._bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            except Exception as e:
                syslog(LOG_ERR, f"Could not connect message bus: {str(e)}")
                self._bus = None
        return self._bus
