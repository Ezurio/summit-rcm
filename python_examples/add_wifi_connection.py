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

s_con = dbus.Dictionary(
    {
        "type": "802-11-wireless",
        "uuid": "7371bb78-c1f7-42a3-a9db-5b9566e8ca07",
        "id": "wfa9",
        "autoconnect": True,
        "interface-name": "wlan0",
    }
)

s_wifi = dbus.Dictionary(
    {
        "ssid": dbus.ByteArray("wfa9".encode("utf-8")),
        "security": "802-11-wireless-security",
    }
)

s_wsec = dbus.Dictionary({"key-mgmt": "wpa-psk", "psk": "arkansas"})

s_ip4 = dbus.Dictionary({"method": "auto"})
s_ip6 = dbus.Dictionary({"method": "auto"})

con = dbus.Dictionary(
    {
        "connection": s_con,
        "802-11-wireless": s_wifi,
        "802-11-wireless-security": s_wsec,
        "ipv4": s_ip4,
        "ipv6": s_ip6,
    }
)


bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_SETTINGS_OBJ)
settings = dbus.Interface(proxy, NM_SETTINGS_IFACE)

settings.AddConnection(con)

added_connection = settings.GetConnectionByUuid(s_con["uuid"])
connection_proxy = bus.get_object(NM_IFACE, added_connection)
connection = dbus.Interface(connection_proxy, NM_CONNECTION_IFACE)
connection_settings = connection.GetSettings()
print("Connection added:")
print("Name: " + connection_settings["connection"]["id"])
print("UUID: " + connection_settings["connection"]["uuid"])

s_con["id"] = "wfa9_updated"
con["connection"] = s_con

connection.Update(con)

updated_connection_settings = connection.GetSettings()
print("Connection updated:")
print("Name: " + updated_connection_settings["connection"]["id"])
print("UUID: " + updated_connection_settings["connection"]["uuid"])
