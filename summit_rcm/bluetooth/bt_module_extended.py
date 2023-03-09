#
# bt_module_extended.py
#
# Bluetooth API for Laird Sentrius IG devices and Summit RCM
#

import logging
from typing import Optional
from ..dbus_manager import DBusManager
from dbus_next import DBusError

from .bt_module import (
    BtMgr,
    DBUS_OBJ_MGR_IFACE,
    BT_OBJ,
    BT_ADAPTER_IFACE,
    BT_OBJ_PATH,
    DBUS_PROP_IFACE,
)


class BtMgrEx(BtMgr):
    """
    Class that manages all bluetooth API functionality
    """

    def __init__(
        self,
        discovery_callback,
        characteristic_property_change_callback,
        connection_callback=None,
        write_notification_callback=None,
        logger: Optional[logging.Logger] = None,
        throw_exceptions=False,
        **kwargs
    ):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        self.logger.info("Initalizing BtMgrEx")
        self.throw_exceptions = throw_exceptions

        self.devices = {}

        # Get DBus objects
        bus = DBusManager.get_bus()
        self.manager = bus.get_proxy_object(
            BT_OBJ, "/", bus.introspect_sync(BT_OBJ, "/")
        ).get_interface(DBUS_OBJ_MGR_IFACE)
        self.adapter = bus.get_proxy_object(
            BT_OBJ, BT_OBJ_PATH, bus.introspect_sync(BT_OBJ, BT_OBJ_PATH)
        ).get_interface(BT_ADAPTER_IFACE)
        self.adapter_props = bus.get_proxy_object(
            BT_OBJ, BT_OBJ_PATH, bus.introspect_sync(BT_OBJ, BT_OBJ_PATH)
        ).get_interface(DBUS_PROP_IFACE)
        self.objects = self.manager.call_get_managed_objects_sync()

        # Register signal handlers
        self.manager.on_interfaces_added(discovery_callback)
        super(BtMgr, self).__init__(**kwargs)

        # Save custom callbacks with the client
        self.characteristic_property_change_callback = (
            characteristic_property_change_callback
        )
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback

        # Power on the bluetooth module
        self.adapter_props.call_set_sync(BT_ADAPTER_IFACE, "Powered", True)


def bt_init_ex(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Optional[BtMgrEx]:
    """
    Initialize the IG bluetooth API
    Returns the device manager instance, to be used in bt_* calls
    """
    try:
        bt = BtMgrEx(
            discovery_callback,
            characteristic_property_change_callback,
            connection_callback,
            write_notification_callback,
            logger,
            **kwargs
        )
        return bt
    except DBusError as e:
        if logger:
            logger.error("Cannot open BT interface: {}".format(e))
        else:
            logging.getLogger(__name__).error("Cannot open BT interface: {}".format(e))
        return None
