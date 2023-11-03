from syslog import syslog, LOG_ERR
from typing import Optional
import os

try:
    from dbus_fast.constants import BusType
    from dbus_fast.aio import MessageBus
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
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
