import dbus

WIFI_DEVICE_NAME = "wlan0"

DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"
NM_SETTINGS_OBJ = "/org/freedesktop/NetworkManager/Settings"
NM_SETTINGS_IFACE = "org.freedesktop.NetworkManager.Settings"
NM_CONNECTION_IFACE = "org.freedesktop.NetworkManager.Settings.Connection"
NM_CONNECTION_ACTIVE_IFACE = "org.freedesktop.NetworkManager.Connection.Active"

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)
manager = dbus.Interface(proxy, NM_IFACE)

wifi_device = manager.GetDeviceByIpIface(WIFI_DEVICE_NAME)
dev_proxy = bus.get_object(NM_IFACE, wifi_device)
prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)

active_connection = prop_iface.Get(NM_DEVICE_IFACE, "ActiveConnection")
active_connection_proxy = bus.get_object(NM_IFACE, active_connection)
active_connection_prop_iface = dbus.Interface(active_connection_proxy, DBUS_PROP_IFACE)
print("Active Connection:")
print("Name: " + active_connection_prop_iface.Get(NM_CONNECTION_ACTIVE_IFACE, "Id"))
print("UUID: " + active_connection_prop_iface.Get(NM_CONNECTION_ACTIVE_IFACE, "Uuid"))
print()

connections = prop_iface.Get(NM_DEVICE_IFACE, "AvailableConnections")
for c in connections:
    connection_proxy = bus.get_object(NM_IFACE, c)
    connection = dbus.Interface(connection_proxy, NM_CONNECTION_IFACE)
    connection_settings = connection.GetSettings()
    print("Connection:")
    print("Name: " + connection_settings["connection"]["id"])
    print("UUID: " + connection_settings["connection"]["uuid"])
