import dbus
import uuid

NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_SETTINGS_OBJ = "/org/freedesktop/NetworkManager/Settings"
NM_SETTINGS_IFACE = "org.freedesktop.NetworkManager.Settings"
NM_CONNECTION_IFACE = "org.freedesktop.NetworkManager.Settings.Connection"

uuid = "6a61efdd-e058-44c9-90c4-0305ce52a8d1"

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_SETTINGS_OBJ)
manager = dbus.Interface(proxy, NM_SETTINGS_IFACE)
connection_for_deletion = manager.GetConnectionByUuid(uuid)
connection_proxy = bus.get_object(NM_IFACE, connection_for_deletion)
connection = dbus.Interface(connection_proxy, NM_CONNECTION_IFACE)
connection_settings = connection.GetSettings()
print("Connection:")
print("Name: " + connection_settings["connection"]["id"])
print("UUID: " + connection_settings["connection"]["uuid"])
