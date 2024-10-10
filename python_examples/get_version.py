#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#

import dbus
import subprocess

# Standard DBUS Properties
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)

print(
    "Build: "
    + subprocess.check_output(["cat", "/etc/os-release"]).decode("ascii").rstrip()
)

# For org.freedesktop.NetworkManager
# Use standard DBUS Property on NetworkManager to
# Get NM version
manager_iface = dbus.Interface(proxy, DBUS_PROP_IFACE)
print("Network Manager Version: " + str(manager_iface.Get(NM_IFACE, "Version")))

# For org.freedesktop.NetworkManager
manager = dbus.Interface(proxy, NM_IFACE)
# Call a NM_IFACE's method
devices = manager.GetDevices()
for d in devices:
    # Get device object
    dev_proxy = bus.get_object(NM_IFACE, d)
    prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
    # Get org.freedesktop.NetworkManager.Device properties
    print("Interface Name: " + str(prop_iface.Get(NM_DEVICE_IFACE, "Interface")))
    driver = prop_iface.Get(NM_DEVICE_IFACE, "Driver")
    print("\tDriver Name: " + str(driver))
    print("\tDriver Version: " + str(prop_iface.Get(NM_DEVICE_IFACE, "DriverVersion")))
    print(
        "\tFirmware Version: " + str(prop_iface.Get(NM_DEVICE_IFACE, "FirmwareVersion"))
    )
    device_type = prop_iface.Get(NM_DEVICE_IFACE, "DeviceType")
    if device_type == 2:
        # Dont know/Cant get supplicant version via NM debus or native supplicant dbus
        print(
            "\tSupplicant: "
            + subprocess.check_output(["sdcsupp", "-v"]).decode("ascii").rstrip()
        )
        # NM driver version only returns kernel version, which matches modinfo vermagic
        print(
            "\tDriver Version: "
            + subprocess.check_output(["modinfo", "--field=version", driver])
            .decode("ascii")
            .rstrip()
        )
