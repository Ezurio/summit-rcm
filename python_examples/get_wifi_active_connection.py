#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#

import dbus

WIFI_DEVICE_NAME = "wlan0"

# Standard DBUS Properties
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"
NM_CONNECTION_ACTIVE_IFACE = "org.freedesktop.NetworkManager.Connection.Active"

NM_ACTIVE_CONNECTION_STATE_UNKNOWN = 0
NM_ACTIVE_CONNECTION_STATE_ACTIVATING = 1
NM_ACTIVE_CONNECTION_STATE_ACTIVATED = 2
NM_ACTIVE_CONNECTION_STATE_DEACTIVATING = 3
NM_ACTIVE_CONNECTION_STATE_DEACTIVATED = 4


def nm_state_to_string(state):
    switcher = {
        NM_ACTIVE_CONNECTION_STATE_UNKNOWN: "State Unknown",
        NM_ACTIVE_CONNECTION_STATE_ACTIVATING: "State activating",
        NM_ACTIVE_CONNECTION_STATE_ACTIVATED: "State activated",
        NM_ACTIVE_CONNECTION_STATE_DEACTIVATING: "State deactivating",
        NM_ACTIVE_CONNECTION_STATE_DEACTIVATED: "State deactivated",
    }
    return switcher.get(state, "Unknown State")


bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)
manager = dbus.Interface(proxy, NM_IFACE)

wifi_device = manager.GetDeviceByIpIface(WIFI_DEVICE_NAME)
dev_proxy = bus.get_object(NM_IFACE, wifi_device)
prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)

wifi_state = prop_iface.Get(NM_DEVICE_IFACE, "State")

active_connection = prop_iface.Get(NM_DEVICE_IFACE, "ActiveConnection")
active_connection_proxy = bus.get_object(NM_IFACE, active_connection)
active_connection_prop_iface = dbus.Interface(active_connection_proxy, DBUS_PROP_IFACE)
active_connection_id = active_connection_prop_iface.Get(
    NM_CONNECTION_ACTIVE_IFACE, "Id"
)
active_connection_uuid = active_connection_prop_iface.Get(
    NM_CONNECTION_ACTIVE_IFACE, "Uuid"
)
active_connection_type = active_connection_prop_iface.Get(
    NM_CONNECTION_ACTIVE_IFACE, "Type"
)
active_connection_state = active_connection_prop_iface.Get(
    NM_CONNECTION_ACTIVE_IFACE, "State"
)

print(WIFI_DEVICE_NAME + " " + nm_state_to_string(active_connection_state))
if active_connection_state == NM_ACTIVE_CONNECTION_STATE_ACTIVATED:
    print("ID: " + active_connection_id)
    print("UUID: " + active_connection_uuid)
    print("Type: " + active_connection_type)
