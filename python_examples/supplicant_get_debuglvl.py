#!/usr/bin/python
import dbus

DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
WPA_OBJ = "/fi/w1/wpa_supplicant1"
WPA_IFACE = "fi.w1.wpa_supplicant1"

bus = dbus.SystemBus()
proxy = bus.get_object(WPA_IFACE, WPA_OBJ)
wpas = dbus.Interface(proxy, DBUS_PROP_IFACE)
debug_level = wpas.Get(WPA_IFACE, "DebugLevel")
print("Current debug level: " + debug_level)
wpas.Set(WPA_IFACE, "DebugLevel", "info")
new_debug_level = wpas.Get(WPA_IFACE, "DebugLevel")
print("New debug level: " + new_debug_level)
