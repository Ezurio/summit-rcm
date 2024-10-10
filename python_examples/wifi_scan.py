#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#

import dbus
import socket, struct
import time

WIFI_DEVICE_NAME = "wlan0"

# Standard DBUS Properties
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"
NM_WIRELESS_IFACE = "org.freedesktop.NetworkManager.Device.Wireless"
NM_ACCESSPOINT_IFACE = "org.freedesktop.NetworkManager.AccessPoint"

NM_802_11_AP_FLAGS_NONE = 0x00000000
NM_802_11_AP_FLAGS_PRIVACY = 0x00000001
NM_802_11_AP_FLAGS_WPS = 0x00000002
NM_802_11_AP_FLAGS_WPS_PBC = 0x00000004
NM_802_11_AP_FLAGS_WPS_PIN = 0x00000008

NM_802_11_AP_SEC_NONE = 0x00000000
NM_802_11_AP_SEC_PAIR_WEP40 = 0x00000001
NM_802_11_AP_SEC_PAIR_WEP104 = 0x00000002
NM_802_11_AP_SEC_PAIR_TKIP = 0x00000004
NM_802_11_AP_SEC_PAIR_CCMP = 0x00000008
NM_802_11_AP_SEC_GROUP_WEP40 = 0x00000010
NM_802_11_AP_SEC_GROUP_WEP104 = 0x00000020
NM_802_11_AP_SEC_GROUP_TKIP = 0x00000040
NM_802_11_AP_SEC_GROUP_CCMP = 0x00000080
NM_802_11_AP_SEC_KEY_MGMT_PSK = 0x00000100
NM_802_11_AP_SEC_KEY_MGMT_802_1X = 0x00000200


def ap_sec_to_str(sec):
    list = []

    if sec & (0x1 | 0x2 | 0x10 | 0x20):
        list.append("WEP")
    if sec & (0x4 | 0x40):
        list.append("WPA")
    if sec & (0x8 | 0x80):
        list.append("WPA2")
    if sec & 0x100:
        list.append("PSK")
    if sec & 0x200:
        list.append("802.1X")

    return list


bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)

# For org.freedesktop.NetworkManager
# Use standard DBUS Property on NetworkManager to
# Get NM version
manager_iface = dbus.Interface(proxy, DBUS_PROP_IFACE)
print("Network Manager Version:" + str(manager_iface.Get(NM_IFACE, "Version")))

# For org.freedesktop.NetworkManager
manager = dbus.Interface(proxy, NM_IFACE)
# Call a NM_IFACE's method
wifi_device = manager.GetDeviceByIpIface(WIFI_DEVICE_NAME)
# Get device object
dev_proxy = bus.get_object(NM_IFACE, wifi_device)
prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
# Get org.freedesktop.NetworkManager.Device properties
print("Interface Name: " + str(prop_iface.Get(NM_DEVICE_IFACE, "Interface")))
# Get a proxy for the wifi interface
wifi_iface = dbus.Interface(dev_proxy, NM_WIRELESS_IFACE)
wifi_prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
# Get the associated AP's object path
wireless_active_access_point = wifi_prop_iface.Get(
    NM_WIRELESS_IFACE, "ActiveAccessPoint"
)
wireless_hwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "HwAddress")
wireless_permhwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "PermHwAddress")
wireless_mode = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "Mode")
# Bitrate identifier will change in next major NM release to "Bitrate"
wireless_bitrate = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "BitRate")
print("Current Access Point:")
print("\tHardware Address:")
print("\t\t" + wireless_hwaddress)
print("\tPermanent Hardware Address:")
print("\t\t" + wireless_permhwaddress)
print("\tMode:")
print("\t\t" + str(int(wireless_mode)))
print("\tBitrate:")
print("\t\t" + str(wireless_bitrate / 1000))

wireless_lastscan = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "LastScan")
print("Last scan:" + str(wireless_lastscan))
difference_in_seconds = (
    (time.clock_gettime(time.CLOCK_MONOTONIC) * 1000) - wireless_lastscan
) / 1000
print("Time difference since last scan: " + str(difference_in_seconds))

# Request scan if last scan is finished
# Dont know how to check if last scan has completed or not
try:
    options = []
    wifi_iface.RequestScan(options)
    print("Scan requested")
except Exception as e:
    print(e)

print("List of all Access Points:")
# Get all APs the card can see
aps = wifi_iface.GetAllAccessPoints()
for path in aps:
    ap_proxy = bus.get_object(NM_IFACE, path)
    ap_prop_iface = dbus.Interface(ap_proxy, DBUS_PROP_IFACE)
    ssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Ssid")
    bssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "HwAddress")
    strength = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Strength")
    maxbitrate = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "MaxBitrate")
    freq = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Frequency")
    flags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Flags")
    wpaflags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "WpaFlags")
    rsnflags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "RsnFlags")
    security_string = "\t\t"
    wpa_flag_string = "\t\t"
    rsn_flag_string = "\t\t"
    print("\tSSID:")
    print("\t\t%s" % "".join([str(v) for v in ssid]))
    print("\tBSSID:")
    print("\t\t" + bssid)
    print("\tStrength:")
    print("\t\t" + str(int(strength)))
    print("\tMax bit rate:")
    print("\t\t" + str(maxbitrate / 1000))
    print("\tFrequency:")
    print("\t\t" + str(freq))
    print("\tFlags:")
    print("\t\t" + str(int(flags)))
    print("\tWPA Flags:")
    print("\t\t" + str(int(wpaflags)))
    print("\tRSN Flags:")
    print("\t\t" + str(int(rsnflags)))
    print("\tWPA Flags String:")
    print("\t\t" + str(ap_sec_to_str(wpaflags)))
    print("\tRSN Flags String:")
    print("\t\t" + str(ap_sec_to_str(rsnflags)))
    print("\tSecurity:")
    # Logic pulled from network-manager/clients/cli/devices.c
    if (
        (flags & NM_802_11_AP_FLAGS_PRIVACY)
        and (wpaflags == NM_802_11_AP_SEC_NONE)
        and (rsnflags == NM_802_11_AP_SEC_NONE)
    ):
        security_string = security_string + "WEP "

    if wpaflags != NM_802_11_AP_SEC_NONE:
        security_string = security_string + "WPA1 "

    if rsnflags != NM_802_11_AP_SEC_NONE:
        security_string = security_string + "WPA2 "

    if (wpaflags & NM_802_11_AP_SEC_KEY_MGMT_802_1X) or (
        rsnflags & NM_802_11_AP_SEC_KEY_MGMT_802_1X
    ):
        security_string = security_string + "802.1X "

    if (wpaflags & NM_802_11_AP_SEC_KEY_MGMT_PSK) or (
        rsnflags & NM_802_11_AP_SEC_KEY_MGMT_PSK
    ):
        security_string = security_string + "PSK"

    print(security_string)

    # Show all flags as human readable.
    if wpaflags & NM_802_11_AP_SEC_PAIR_WEP40:
        wpa_flag_string = wpa_flag_string + "WEP40 "

    if wpaflags & NM_802_11_AP_SEC_PAIR_WEP104:
        wpa_flag_string = wpa_flag_string + "WEP104 "

    if wpaflags & NM_802_11_AP_SEC_PAIR_TKIP:
        wpa_flag_string = wpa_flag_string + "TKIP "

    if wpaflags & NM_802_11_AP_SEC_PAIR_CCMP:
        wpa_flag_string = wpa_flag_string + "CCMP "

    if wpaflags & NM_802_11_AP_SEC_GROUP_WEP40:
        wpa_flag_string = wpa_flag_string + "GROUP_WEP40 "

    if wpaflags & NM_802_11_AP_SEC_GROUP_WEP104:
        wpa_flag_string = wpa_flag_string + "GROUP_WEP104 "

    if wpaflags & NM_802_11_AP_SEC_GROUP_TKIP:
        wpa_flag_string = wpa_flag_string + "GROUP_TKIP "

    if wpaflags & NM_802_11_AP_SEC_GROUP_CCMP:
        wpa_flag_string = wpa_flag_string + "GROUP_CCMP "

    if wpaflags & NM_802_11_AP_SEC_KEY_MGMT_802_1X:
        wpa_flag_string = wpa_flag_string + "802.1X "

    print("\tWPA Security Flags:")
    print(wpa_flag_string)

    if rsnflags & NM_802_11_AP_SEC_PAIR_WEP40:
        rsn_flag_string = rsn_flag_string + "WEP40 "

    if rsnflags & NM_802_11_AP_SEC_PAIR_WEP104:
        rsn_flag_string = rsn_flag_string + "WEP104 "

    if rsnflags & NM_802_11_AP_SEC_PAIR_TKIP:
        rsn_flag_string = rsn_flag_string + "TKIP "

    if rsnflags & NM_802_11_AP_SEC_PAIR_CCMP:
        rsn_flag_string = rsn_flag_string + "CCMP "

    if rsnflags & NM_802_11_AP_SEC_GROUP_WEP40:
        rsn_flag_string = rsn_flag_string + "GROUP_WEP40 "

    if rsnflags & NM_802_11_AP_SEC_GROUP_WEP104:
        rsn_flag_string = rsn_flag_string + "GROUP_WEP104 "

    if rsnflags & NM_802_11_AP_SEC_GROUP_TKIP:
        rsn_flag_string = rsn_flag_string + "GROUP_TKIP "

    if rsnflags & NM_802_11_AP_SEC_GROUP_CCMP:
        rsn_flag_string = rsn_flag_string + "GROUP_CCMP "

    if rsnflags & NM_802_11_AP_SEC_KEY_MGMT_802_1X:
        rsn_flag_string = rsn_flag_string + "802.1X "

    print("\tRSN Security Flags:")
    print(rsn_flag_string)
    print()
