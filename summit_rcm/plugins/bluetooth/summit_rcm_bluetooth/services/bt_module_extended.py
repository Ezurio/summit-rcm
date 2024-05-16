"""
bt_module_extended.py

Bluetooth API for Sentrius IG devices and Summit RCM
"""

import logging
from typing import Optional
from dbus_fast import DBusError
from summit_rcm.dbus_manager import DBusManager
from summit_rcm_bluetooth.services.bt_module import (
    BtMgr,
    DBUS_OBJ_MGR_IFACE,
    BT_OBJ,
    BT_ADAPTER_IFACE,
    BT_OBJ_PATH,
)


class BtMgrEx(BtMgr):
    """
    Class that manages all bluetooth API functionality
    """

    def __init__(
        self,
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

        # Call base constructor
        super(BtMgr, self).__init__(**kwargs)

        # Save custom callbacks with the client
        self.characteristic_property_change_callback = (
            characteristic_property_change_callback
        )
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback


async def create_bt_mgr_ex(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
    logger: Optional[logging.Logger] = None,
    throw_exceptions=False,
    **kwargs
) -> BtMgrEx:
    """
    Async wrapper to create a BtMgrEx object
    """

    bt_mgr_ex = BtMgrEx(
        characteristic_property_change_callback,
        connection_callback,
        write_notification_callback,
        logger,
        throw_exceptions,
        **kwargs
    )

    # Get DBus objects
    bus = await DBusManager().get_bus()
    bt_mgr_ex.manager = bus.get_proxy_object(
        BT_OBJ, "/", await bus.introspect(BT_OBJ, "/")
    ).get_interface(DBUS_OBJ_MGR_IFACE)
    bt_mgr_ex.adapter = bus.get_proxy_object(
        BT_OBJ, BT_OBJ_PATH, await bus.introspect(BT_OBJ, BT_OBJ_PATH)
    ).get_interface(BT_ADAPTER_IFACE)
    bt_mgr_ex.objects = await bt_mgr_ex.manager.call_get_managed_objects()

    # Register signal handlers
    bt_mgr_ex.manager.on_interfaces_added(discovery_callback)

    # Power on the bluetooth module
    await bt_mgr_ex.adapter.set_powered(True)

    return bt_mgr_ex


async def bt_init_ex(
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
        bt = await create_bt_mgr_ex(
            discovery_callback,
            characteristic_property_change_callback,
            connection_callback,
            write_notification_callback,
            logger,
            **kwargs
        )
        return bt
    except DBusError as exception:
        if logger:
            logger.error("Cannot open BT interface: %s", exception)
        else:
            logging.getLogger(__name__).error("Cannot open BT interface: %s", exception)
        return None
