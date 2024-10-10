#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#

import dbus

NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_SETTINGS_OBJ = "/org/freedesktop/NetworkManager/Settings"
NM_SETTINGS_IFACE = "org.freedesktop.NetworkManager.Settings"
NM_CONNECTION_IFACE = "org.freedesktop.NetworkManager.Settings.Connection"

CONNECTION_TO_REMOVE = "wfa9"

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_SETTINGS_OBJ)
manager = dbus.Interface(proxy, NM_SETTINGS_IFACE)
connections = manager.ListConnections()
for c in connections:
    connection_proxy = bus.get_object(NM_IFACE, c)
    connection = dbus.Interface(connection_proxy, NM_CONNECTION_IFACE)
    connection_settings = connection.GetSettings()
    print("Found connection:")
    print("Name: " + connection_settings["connection"]["id"])
    print("UUID: " + connection_settings["connection"]["uuid"])
    if connection_settings["connection"]["id"] == CONNECTION_TO_REMOVE:
        connection.Delete()
        print()
        print("Connection " + connection_settings["connection"]["id"] + " deleted!")
        print()
